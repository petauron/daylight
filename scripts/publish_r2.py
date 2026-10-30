#!/usr/bin/env python3
"""Verify private Release assets and copy the two archives to R2 using runner tools."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def publish(tag, directory, metadata_path):
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:-alpha\.[0-9]+)?", tag):
        raise ValueError("invalid release tag")
    directory = Path(directory)
    release = json.loads(Path(metadata_path).read_text())
    archives = {f"daylight-{tag}-linux-{arch}.tar.gz" for arch in ("amd64", "arm64")}
    expected = archives | {"release.json", "SHA256SUMS"}
    assets = release.get("assets", [])
    if release.get("tag_name") != tag or len(assets) != len(expected) or {a["name"] for a in assets} != expected:
        raise ValueError("unexpected Release asset inventory")
    if {p.name for p in directory.iterdir()} != expected:
        raise ValueError("unexpected local asset inventory")
    digests = {}
    for asset in assets:
        path = directory / asset["name"]
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 64 * 1024 * 1024:
            raise ValueError("invalid Release asset")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if asset.get("digest") != "sha256:" + digest or asset.get("size") != path.stat().st_size:
            raise ValueError("downloaded Release asset differs")
        digests[path.name] = digest
    inventory = json.loads((directory / "release.json").read_text())
    expected_archives = {name: digests[name] for name in sorted(archives)}
    if inventory.get("version") != tag[1:] or inventory.get("archives") != expected_archives:
        raise ValueError("Release version or archive inventory differs")
    sums = "".join(digest + "  " + name + "\n" for name, digest in sorted(expected_archives.items()))
    if (directory / "SHA256SUMS").read_text() != sums:
        raise ValueError("checksum inventory differs")
    bucket, endpoint = os.environ.get("R2_BUCKET_NAME", ""), os.environ.get("R2_ENDPOINT", "")
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]+", bucket) or not re.fullmatch(r"https://[a-z0-9]+\.r2\.cloudflarestorage\.com", endpoint):
        raise ValueError("missing or invalid R2 destination")
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        raise ValueError("R2 repository secrets are not configured")

    def aws(*args):
        return subprocess.run(["aws", "--cli-connect-timeout", "10", "--cli-read-timeout", "60",
                               "--endpoint-url", endpoint, "s3api", *args, "--bucket", bucket,
                               "--no-cli-pager"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with tempfile.TemporaryDirectory(prefix="daylight-r2-") as temporary:
        for name in sorted(archives):
            key = "daylight/" + tag + "/" + name
            # Never overwrite an existing object. An idempotent retry is valid only
            # when a subsequent read returns the exact expected bytes.
            aws("put-object", "--key", key, "--body", str(directory / name),
                "--if-none-match", "*", "--content-type", "application/gzip",
                "--cache-control", "public,max-age=31536000,immutable")
            readback = Path(temporary) / name
            if aws("get-object", "--key", key, str(readback)).returncode != 0:
                raise ValueError("R2 write/read-back failed")
            if hashlib.sha256(readback.read_bytes()).hexdigest() != digests[name]:
                raise ValueError("R2 object conflicts with the verified Release")
    print("R2 archive distribution verified for " + tag)


if __name__ == "__main__":
    try:
        if len(sys.argv) != 4:
            raise ValueError("usage: publish_r2.py tag directory release-metadata.json")
        publish(*sys.argv[1:])
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        # Never print provider stderr, credentials or complete environment values.
        print("Daylight distribution failed: " + str(error) if isinstance(error, ValueError) else "Daylight distribution failed", file=sys.stderr)
        sys.exit(1)
