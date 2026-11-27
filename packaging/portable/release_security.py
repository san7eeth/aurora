"""Fail-closed Ed25519 and SHA-256 verification for Aurora release artifacts."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import PurePosixPath

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def canonical_manifest(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def validate_signing_keys(private_key_file: str, public_key_file: str, expected_fingerprint: str) -> str:
    with open(private_key_file, "rb") as private_file:
        private = serialization.load_pem_private_key(private_file.read(), password=None)
    with open(public_key_file, "rb") as public_file:
        public = serialization.load_pem_public_key(public_file.read())
    if not isinstance(private, Ed25519PrivateKey) or not isinstance(public, Ed25519PublicKey):
        raise ValueError("Release keys must be Ed25519 PEM keys")
    raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    private_raw = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    if private_raw != raw:
        raise ValueError("Private signing key does not match the supplied public key")
    fingerprint = hashlib.sha256(raw).hexdigest()
    if fingerprint.lower() != expected_fingerprint.replace(":", "").lower():
        raise ValueError("Signing key fingerprint does not match AURORA_RELEASE_KEY_FINGERPRINT")
    return fingerprint


def create_reproducible_zip(staged_root: str, destination: str) -> None:
    from pathlib import Path

    root_path = Path(staged_root).resolve()
    if root_path.name != "Aurora":
        raise ValueError("Portable ZIP staging directory must be named Aurora")
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for path in sorted(root_path.rglob("*"), key=lambda item: item.relative_to(root_path).as_posix()):
            if path.is_symlink():
                raise ValueError(f"Staging tree contains a symbolic link: {path}")
            if not path.is_file():
                continue
            relative = path.relative_to(root_path).as_posix()
            info = zipfile.ZipInfo(f"{root_path.name}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0x20
            package.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def create_unsigned_candidate_manifest(staged_root: str, version: str) -> None:
    from pathlib import Path

    root_path = Path(staged_root).resolve()
    if root_path.name != "Aurora":
        raise ValueError("Portable ZIP staging directory must be named Aurora")
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
        raise ValueError("Version must use semantic version form MAJOR.MINOR.PATCH")
    if (root_path / "release_manifest.sig").exists():
        raise ValueError("Unsigned candidates must not contain a signature")

    files = {}
    for path in sorted(root_path.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Staging tree contains a symbolic link: {path}")
        if path.is_file() and path.name not in {"release_manifest.json", "release_manifest.sig", "SHA256SUMS.txt"}:
            files[path.relative_to(root_path).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()

    checksums = "".join(f"{digest}  {name}\n" for name, digest in files.items())
    (root_path / "SHA256SUMS.txt").write_text(checksums, encoding="ascii")
    files["SHA256SUMS.txt"] = hashlib.sha256((root_path / "SHA256SUMS.txt").read_bytes()).hexdigest()
    timestamp = os.environ.get("AURORA_BUILD_TIMESTAMP_UTC")
    if not timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    release_id = os.environ.get(
        "AURORA_RELEASE_ID", f"v{version}-UNSIGNED-RC-{timestamp.replace(':', '').replace('-', '')}"
    )
    release_notes = os.environ.get("AURORA_RELEASE_NOTES", "Unsigned release candidate; not trusted for installation.")
    if len(release_notes) > 12000:
        release_notes = release_notes[:12000]
    manifest = {
        "product": "Aurora",
        "version": version,
        "architecture": "Windows-x64",
        "release_type": "UNSIGNED-RC",
        "release_id": release_id,
        "build_timestamp_utc": timestamp,
        "files": files,
        "release_notes": release_notes,
    }
    (root_path / "release_manifest.json").write_bytes(canonical_manifest(manifest) + b"\n")


def verify_unsigned_candidate(archive: str) -> dict:
    with zipfile.ZipFile(archive) as package:
        infos = package.infolist()
        names = [entry.filename for entry in infos]
        if len(names) != len(set(names)):
            raise ValueError("ZIP contains duplicate paths")
        for entry in infos:
            name = entry.filename
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
                raise ValueError(f"Unsafe ZIP path: {name}")
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError(f"ZIP contains a symbolic link: {name}")
            if not name.startswith("Aurora/"):
                raise ValueError(f"Unexpected top-level ZIP path: {name}")
            relative = path.parts[1:]
            if any(part.lower() == ".git" for part in relative):
                raise ValueError(f"Git metadata must not be packaged: {name}")
            if path.suffix.lower() in {".py", ".pyc", ".pyo", ".pyi", ".db", ".sqlite", ".sqlite3"}:
                raise ValueError(f"Development source or user database must not be packaged: {name}")
            if path.name.lower() == ".env" or path.name.lower().endswith(".env"):
                raise ValueError(f"Environment secrets must not be packaged: {name}")

        if package.testzip() is not None:
            raise ValueError("ZIP CRC validation failed")
        if "Aurora/release_manifest.sig" in names:
            raise ValueError("Unsigned candidates must not contain a signature")
        manifest = json.loads(package.read("Aurora/release_manifest.json"))
        if manifest.get("release_type") != "UNSIGNED-RC":
            raise ValueError("Manifest is not clearly labelled UNSIGNED-RC")
        if manifest.get("product") != "Aurora" or manifest.get("architecture") != "Windows-x64":
            raise ValueError("Manifest product or architecture is unsupported")
        version = manifest.get("version")
        if not isinstance(version, str) or not re.fullmatch(
            r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version
        ):
            raise ValueError("Manifest version is not MAJOR.MINOR.PATCH")
        timestamp = manifest.get("build_timestamp_utc")
        if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
            raise ValueError("Manifest build timestamp is invalid")
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp[:-1] + "+00:00")
        except ValueError as exc:
            raise ValueError("Manifest build timestamp is invalid") from exc
        if parsed_timestamp.utcoffset() != timezone.utc.utcoffset(parsed_timestamp):
            raise ValueError("Manifest build timestamp must be UTC")

        expected = manifest.get("files")
        if not isinstance(expected, dict) or not expected:
            raise ValueError("Manifest has no file hashes")
        packaged_files = {
            name[len("Aurora/"):]
            for name in names
            if name.startswith("Aurora/") and not name.endswith("/")
        } - {"release_manifest.json"}
        if set(expected) != packaged_files:
            raise ValueError("ZIP contains unlisted files or the manifest lists missing files")
        for name, digest in expected.items():
            if (not isinstance(name, str) or PurePosixPath(name).is_absolute()
                    or "\\" in name or ":" in name or ".." in PurePosixPath(name).parts):
                raise ValueError(f"Unsafe manifest path: {name}")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError(f"Invalid SHA-256 digest for {name}")
            if hashlib.sha256(package.read("Aurora/" + name)).hexdigest() != digest:
                raise ValueError(f"Missing or modified release file: {name}")
        checksum_lines = package.read("Aurora/SHA256SUMS.txt").decode("ascii").splitlines()
        checksums = {}
        for line in checksum_lines:
            parts = line.split("  ", 1)
            if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
                raise ValueError("Malformed SHA256SUMS.txt entry")
            checksums[parts[1]] = parts[0]
        signed_hashes = {name: digest for name, digest in expected.items() if name != "SHA256SUMS.txt"}
        if checksums != signed_hashes:
            raise ValueError("SHA256SUMS.txt does not match the candidate manifest")
    return manifest


def verify_zip(archive: str, public_key_file: str, expected_fingerprint: str) -> dict:
    with open(public_key_file, "rb") as key_file:
        key_bytes = key_file.read()
    public = serialization.load_pem_public_key(key_bytes)
    if not isinstance(public, Ed25519PublicKey):
        raise ValueError("Trusted key is not Ed25519")
    raw_key = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    fingerprint = hashlib.sha256(raw_key).hexdigest()
    if fingerprint.lower() != expected_fingerprint.replace(":", "").lower():
        raise ValueError("Public-key fingerprint does not match the independently trusted fingerprint")

    with zipfile.ZipFile(archive) as package:
        infos = package.infolist()
        names = [entry.filename for entry in infos]
        if len(names) != len(set(names)):
            raise ValueError("ZIP contains duplicate paths")
        for entry in infos:
            name = entry.filename
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
                raise ValueError(f"Unsafe ZIP path: {name}")
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError(f"ZIP contains a symbolic link: {name}")
            if not name.startswith("Aurora/"):
                raise ValueError(f"Unexpected top-level ZIP path: {name}")
        manifest_path = "Aurora/release_manifest.json"
        signature_path = "Aurora/release_manifest.sig"
        if package.getinfo(manifest_path).file_size > 1024 * 1024:
            raise ValueError("Release manifest is unexpectedly large")
        manifest = json.loads(package.read(manifest_path))
        signature = package.read(signature_path)
        if len(signature) != 64:
            raise ValueError("Ed25519 manifest signature has an invalid length")
        public.verify(signature, canonical_manifest(manifest))
        if manifest.get("key_fingerprint") != fingerprint:
            raise ValueError("Manifest signing key fingerprint mismatch")
        version = manifest.get("version")
        if not isinstance(version, str) or not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
            raise ValueError("Manifest version is not MAJOR.MINOR.PATCH")
        if manifest.get("product") != "Aurora" or manifest.get("architecture") != "Windows-x64":
            raise ValueError("Manifest product or architecture is unsupported")
        if not isinstance(manifest.get("release_id"), str) or not manifest["release_id"]:
            raise ValueError("Manifest release identifier is missing")
        timestamp = manifest.get("build_timestamp_utc")
        if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
            raise ValueError("Manifest build timestamp is invalid")
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp[:-1] + "+00:00")
        except ValueError as exc:
            raise ValueError("Manifest build timestamp is invalid") from exc
        if parsed_timestamp.utcoffset() != timezone.utc.utcoffset(parsed_timestamp):
            raise ValueError("Manifest build timestamp must be UTC")
        if not isinstance(manifest.get("release_notes"), str):
            raise ValueError("Manifest release notes are missing")
        expected = manifest.get("files")
        if not isinstance(expected, dict) or not expected:
            raise ValueError("Manifest has no file hashes")
        packaged_files = {
            name[len("Aurora/"):]
            for name in names
            if name.startswith("Aurora/") and not name.endswith("/")
        } - {"release_manifest.json", "release_manifest.sig"}
        if set(expected) != packaged_files:
            raise ValueError("ZIP contains unlisted files or the manifest lists missing files")
        for name, digest in expected.items():
            if (not isinstance(name, str) or PurePosixPath(name).is_absolute()
                    or "\\" in name or ":" in name or ".." in PurePosixPath(name).parts):
                raise ValueError(f"Unsafe manifest path: {name}")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError(f"Invalid SHA-256 digest for {name}")
            if hashlib.sha256(package.read("Aurora/" + name)).hexdigest() != digest:
                raise ValueError(f"Missing or modified release file: {name}")
        checksum_lines = package.read("Aurora/SHA256SUMS.txt").decode("ascii").splitlines()
        checksums = {}
        for line in checksum_lines:
            parts = line.split("  ", 1)
            if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
                raise ValueError("Malformed SHA256SUMS.txt entry")
            checksums[parts[1]] = parts[0]
        signed_hashes = {name: digest for name, digest in expected.items() if name != "SHA256SUMS.txt"}
        if checksums != signed_hashes:
            raise ValueError("SHA256SUMS.txt does not match the signed manifest")
    return manifest


def sign_staged_package(root: str, private_key_file: str, public_key_file: str, version: str, expected_fingerprint: str) -> None:
    from pathlib import Path
    root_path = Path(root).resolve()
    fingerprint = validate_signing_keys(private_key_file, public_key_file, expected_fingerprint)
    with open(private_key_file, "rb") as private_file:
        private = serialization.load_pem_private_key(private_file.read(), password=None)
    files = {}
    for path in sorted(root_path.rglob("*")):
        if path.is_file() and path.name not in {"release_manifest.json", "release_manifest.sig", "SHA256SUMS.txt"}:
            files[path.relative_to(root_path).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    (root_path / "SHA256SUMS.txt").write_text("".join(f"{digest}  {name}\n" for name, digest in files.items()), encoding="utf-8")
    files["SHA256SUMS.txt"] = hashlib.sha256((root_path / "SHA256SUMS.txt").read_bytes()).hexdigest()
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
        raise ValueError("Version must use semantic version form MAJOR.MINOR.PATCH")
    timestamp = os.environ.get("AURORA_BUILD_TIMESTAMP_UTC")
    if not timestamp:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    release_id = os.environ.get("AURORA_RELEASE_ID", f"v{version}-{timestamp.replace(':', '').replace('-', '')}")
    release_notes = os.environ.get("AURORA_RELEASE_NOTES", "See the bundled CHANGELOG.md.")
    if len(release_notes) > 12000:
        release_notes = release_notes[:12000]
    manifest = {
        "product": "Aurora",
        "version": version,
        "architecture": "Windows-x64",
        "release_id": release_id,
        "build_timestamp_utc": timestamp,
        "files": files,
        "key_fingerprint": fingerprint,
        "release_notes": release_notes,
    }
    body = canonical_manifest(manifest)
    (root_path / "release_manifest.json").write_bytes(body + b"\n")
    (root_path / "release_manifest.sig").write_bytes(private.sign(body))
