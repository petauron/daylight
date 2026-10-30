#!/usr/bin/env python3
"""Build immutable Daylight archives; no third-party Python dependency."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import urllib.request

root = Path(__file__).resolve().parents[1]
version = (root / "VERSION").read_text().strip()
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-alpha\.[0-9]+)?", version):
    raise SystemExit("invalid release version")
lock = json.loads((root / "release/caddy.json").read_text())
out = root / "dist"
out.mkdir(exist_ok=True)
inventory = {}
for arch in ("amd64", "arm64"):
    source = lock["archives"][arch]
    with urllib.request.urlopen(source["url"], timeout=90) as response:
        raw = response.read(64 * 1024 * 1024 + 1)
    if len(raw) > 64 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != source["sha256"]:
        raise SystemExit("Caddy archive verification failed")
    with tempfile.TemporaryDirectory(prefix="daylight-package-") as temporary:
        binary = Path(temporary) / "daylight"
        env = dict(os.environ, GOOS="linux", GOARCH=arch, CGO_ENABLED="0", GOTOOLCHAIN="local")
        subprocess.run(["go", "build", "-trimpath", "-ldflags", "-s -w -X main.version=" + version,
                        "-o", str(binary), "."], cwd=root, env=env, check=True)
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as upstream:
            entries = upstream.getmembers()
            members = {member.name: member for member in entries}
            if len(members) != len(entries):
                raise SystemExit("duplicate upstream archive member")
            payload = {"daylight": binary.read_bytes(), "README.md": (root / "README.md").read_bytes(),
                       "examples/site.json": (root / "examples/site.json").read_bytes()}
            for name, destination in (("caddy", "caddy"), ("LICENSE", "LICENSE"), ("README.md", "CADDY-README.md")):
                member = members.get(name)
                if member is None or not member.isfile() or member.size > 64 * 1024 * 1024:
                    raise SystemExit("invalid upstream archive member")
                payload[destination] = upstream.extractfile(member).read()
        name = "daylight-v" + version + "-linux-" + arch + ".tar.gz"
        with (out / name).open("wb") as destination:
            with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w") as archive:
                    for path, content in sorted(payload.items()):
                        entry = tarfile.TarInfo(path)
                        entry.size = len(content)
                        entry.mode = 0o755 if path in ("caddy", "daylight") else 0o644
                        archive.addfile(entry, io.BytesIO(content))
        inventory[name] = hashlib.sha256((out / name).read_bytes()).hexdigest()
(out / "SHA256SUMS").write_text("".join(digest + "  " + name + "\n" for name, digest in sorted(inventory.items())))
(out / "release.json").write_text(json.dumps({"version": version, "caddy": lock["version"], "archives": inventory}, indent=2) + "\n")
