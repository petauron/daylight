#!/usr/bin/env python3
"""Build immutable Daylight archives; no third-party Python dependency."""
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request


MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
ARCHITECTURES = ("amd64", "arm64")


def _read_verified_cache(cache_path: Path, expected_sha: str) -> bytes | None:
    open_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = None
    try:
        fd = os.open(str(cache_path), open_flags)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ARCHIVE_BYTES:
            return None
        handle = os.fdopen(fd, "rb")
        fd = None
        with handle:
            cached = handle.read(MAX_ARCHIVE_BYTES + 1)
        if len(cached) <= MAX_ARCHIVE_BYTES and hashlib.sha256(cached).hexdigest() == expected_sha:
            return cached
        return None
    except OSError:
        return None
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


def _write_cache_best_effort(cache_path: Path, arch: str, raw: bytes) -> None:
    fd = None
    tmp_path = None
    try:
        fd, tmp_name = tempfile.mkstemp(prefix=f".caddy-{arch}-", dir=str(cache_path.parent))
        tmp_path = Path(tmp_name)
        handle = os.fdopen(fd, "wb")
        fd = None
        with handle:
            handle.write(raw)
        os.replace(tmp_path, cache_path)
        tmp_path = None
    except OSError as exc:
        print(f"warning: skipping Caddy cache write for {arch}: {exc}", file=sys.stderr)
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass


def load_verified_caddy_archive(caddy_version: str, arch: str, source: dict) -> bytes:
    """Load pinned Caddy archive from verified local cache or upstream URL."""
    expected_sha = source["sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise SystemExit("invalid Caddy archive checksum in release/caddy.json")

    cache_root = os.environ.get("DAYLIGHT_CADDY_CACHE_DIR", "").strip()
    cache_path = None
    if cache_root:
        cache_dir = Path(cache_root)
        try:
            if not cache_dir.is_symlink():
                cache_dir.mkdir(parents=True, exist_ok=True)
                if not cache_dir.is_symlink() and cache_dir.is_dir():
                    cache_path = cache_dir / f"caddy-{caddy_version}-linux-{arch}-{expected_sha}.tar.gz"
                    cached = _read_verified_cache(cache_path, expected_sha)
                    if cached is not None:
                        return cached
        except OSError:
            cache_path = None

    with urllib.request.urlopen(source["url"], timeout=90) as response:
        raw = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(raw) > MAX_ARCHIVE_BYTES or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise SystemExit("Caddy archive verification failed")

    if cache_path is not None:
        _write_cache_best_effort(cache_path, arch, raw)

    return raw


def build_arch_archive(
    root: Path,
    out: Path,
    version: str,
    caddy_version: str,
    arch: str,
    source: dict,
    static_files: dict[str, bytes],
) -> tuple[str, str]:
    raw = load_verified_caddy_archive(caddy_version, arch, source)
    with tempfile.TemporaryDirectory(prefix=f"daylight-package-{arch}-") as temporary:
        binary = Path(temporary) / "daylight"
        env = dict(os.environ, GOOS="linux", GOARCH=arch, CGO_ENABLED="0", GOTOOLCHAIN="local")
        subprocess.run(
            [
                "go",
                "build",
                "-trimpath",
                "-ldflags",
                "-s -w -X main.version=" + version,
                "-o",
                str(binary),
                ".",
            ],
            cwd=root,
            env=env,
            check=True,
        )
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as upstream:
            entries = upstream.getmembers()
            members = {member.name: member for member in entries}
            if len(members) != len(entries):
                raise SystemExit("duplicate upstream archive member")
            payload = {"daylight": binary.read_bytes(), **static_files}
            for name, destination in (
                ("caddy", "caddy"),
                ("LICENSE", "LICENSE"),
                ("README.md", "CADDY-README.md"),
            ):
                member = members.get(name)
                if member is None or not member.isfile() or member.size > MAX_ARCHIVE_BYTES:
                    raise SystemExit("invalid upstream archive member")
                extracted = upstream.extractfile(member)
                if extracted is None:
                    raise SystemExit("invalid upstream archive member")
                payload[destination] = extracted.read()

        name = "daylight-v" + version + "-linux-" + arch + ".tar.gz"
        archive_path = out / name
        with archive_path.open("wb") as destination:
            with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w") as archive:
                    for path, content in sorted(payload.items()):
                        entry = tarfile.TarInfo(path)
                        entry.size = len(content)
                        entry.mode = 0o755 if path in ("caddy", "daylight") else 0o644
                        archive.addfile(entry, io.BytesIO(content))
        digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        return name, digest


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    version = (root / "version.txt").read_text().strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-alpha\.[0-9]+)?", version):
        raise SystemExit("invalid release version")
    lock = json.loads((root / "release/caddy.json").read_text())
    caddy_version = lock["version"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", caddy_version):
        raise SystemExit("invalid Caddy version")
    out = root / "dist"
    out.mkdir(exist_ok=True)
    static_files = {
        "README.md": (root / "README.md").read_bytes(),
        "examples/site.json": (root / "examples/site.json").read_bytes(),
        "site/index.html": (root / "site/index.html").read_bytes(),
    }

    with ThreadPoolExecutor(max_workers=len(ARCHITECTURES)) as pool:
        futures = [
            pool.submit(
                build_arch_archive,
                root,
                out,
                version,
                caddy_version,
                arch,
                lock["archives"][arch],
                static_files,
            )
            for arch in ARCHITECTURES
        ]
        results = [future.result() for future in futures]

    inventory = dict(results)
    (out / "SHA256SUMS").write_text(
        "".join(digest + "  " + name + "\n" for name, digest in sorted(inventory.items()))
    )
    (out / "release.json").write_text(
        json.dumps({"version": version, "caddy": caddy_version, "archives": inventory}, indent=2)
        + "\n"
    )


if __name__ == "__main__":
    main()
