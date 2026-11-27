import hashlib
import json
import sys
import zipfile

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "packaging" / "portable"))
from release_security import (  # noqa: E402
    canonical_manifest,
    create_unsigned_candidate_manifest,
    create_reproducible_zip,
    sign_staged_package,
    verify_unsigned_candidate,
    verify_zip,
)


def make_release(tmp_path, tamper=False, invalid_signature=False):
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    key_file = tmp_path / "public.pem"
    key_file.write_bytes(public.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    fingerprint = hashlib.sha256(raw).hexdigest()
    payload = b"approved executable bytes"
    checksums = f"{hashlib.sha256(payload).hexdigest()}  Aurora.exe\n".encode()
    files = {
        "Aurora.exe": hashlib.sha256(payload).hexdigest(),
        "SHA256SUMS.txt": hashlib.sha256(checksums).hexdigest(),
    }
    manifest = {
        "product": "Aurora",
        "version": "1.0.0",
        "architecture": "Windows-x64",
        "release_id": "v1.0.0-test",
        "build_timestamp_utc": "2026-11-27T00:00:00Z",
        "files": files,
        "key_fingerprint": fingerprint,
        "release_notes": "Test release",
    }
    signature = b"\0" * 64 if invalid_signature else private.sign(canonical_manifest(manifest))
    package_file = tmp_path / "release.zip"
    with zipfile.ZipFile(package_file, "w") as package:
        package.writestr("Aurora/Aurora.exe", payload + (b"tampered" if tamper else b""))
        package.writestr("Aurora/SHA256SUMS.txt", checksums)
        package.writestr("Aurora/release_manifest.json", json.dumps(manifest))
        package.writestr("Aurora/release_manifest.sig", signature)
    return package_file, key_file, fingerprint


def test_release_signature_and_hashes_verify(tmp_path):
    archive, key, fingerprint = make_release(tmp_path)
    assert verify_zip(str(archive), str(key), fingerprint)["version"] == "1.0.0"


def test_modified_release_is_rejected(tmp_path):
    archive, key, fingerprint = make_release(tmp_path, tamper=True)
    with pytest.raises(ValueError, match="modified"):
        verify_zip(str(archive), str(key), fingerprint)


def test_wrong_pinned_fingerprint_is_rejected(tmp_path):
    archive, key, _fingerprint = make_release(tmp_path)
    with pytest.raises(ValueError, match="fingerprint"):
        verify_zip(str(archive), str(key), "00" * 32)


def test_staged_package_is_signed_with_pinned_key_and_verified(tmp_path):
    source = tmp_path / "Aurora"
    source.mkdir()
    (source / "Aurora.exe").write_bytes(b"payload")
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    private_file = tmp_path / "private.pem"
    public_file = tmp_path / "public.pem"
    private_file.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    public_file.write_bytes(public.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    fingerprint = hashlib.sha256(public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).hexdigest()

    sign_staged_package(str(source), str(private_file), str(public_file), "1.0.0", fingerprint)
    archive = tmp_path / "signed.zip"
    second_archive = tmp_path / "signed-second.zip"
    create_reproducible_zip(str(source), str(archive))
    create_reproducible_zip(str(source), str(second_archive))
    assert archive.read_bytes() == second_archive.read_bytes()
    manifest = verify_zip(str(archive), str(public_file), fingerprint)
    assert manifest["version"] == "1.0.0"
    assert manifest["architecture"] == "Windows-x64"
    assert manifest["release_id"]
    assert manifest["build_timestamp_utc"].endswith("Z")


def test_zip_slip_path_is_rejected(tmp_path):
    archive, key, fingerprint = make_release(tmp_path)
    with zipfile.ZipFile(archive, "a") as package:
        package.writestr("Aurora/../outside.txt", "unsafe")
    with pytest.raises(ValueError, match="Unsafe ZIP path"):
        verify_zip(str(archive), str(key), fingerprint)


def test_invalid_signature_is_rejected(tmp_path):
    archive, key, fingerprint = make_release(tmp_path, invalid_signature=True)
    with pytest.raises(InvalidSignature):
        verify_zip(str(archive), str(key), fingerprint)


def test_unsupported_archive_root_is_rejected(tmp_path):
    archive, key, fingerprint = make_release(tmp_path)
    with zipfile.ZipFile(archive, "a") as package:
        package.writestr("outside.txt", b"unlisted")
    with pytest.raises(ValueError, match="top-level"):
        verify_zip(str(archive), str(key), fingerprint)


def test_unsigned_candidate_has_explicit_label_and_verified_hashes(tmp_path):
    source = tmp_path / "Aurora"
    source.mkdir()
    (source / "Aurora.exe").write_bytes(b"candidate executable")
    runtime = source / "runtime"
    runtime.mkdir()
    (runtime / "required.dll").write_bytes(b"runtime")
    create_unsigned_candidate_manifest(str(source), "1.2.3")

    archive = tmp_path / "Aurora-UNSIGNED-RC.zip"
    create_reproducible_zip(str(source), str(archive))
    manifest = verify_unsigned_candidate(str(archive))

    assert manifest["release_type"] == "UNSIGNED-RC"
    assert manifest["version"] == "1.2.3"
    with zipfile.ZipFile(archive) as package:
        assert "Aurora/release_manifest.sig" not in package.namelist()


def test_unsigned_candidate_rejects_modified_payload(tmp_path):
    source = tmp_path / "Aurora"
    source.mkdir()
    (source / "Aurora.exe").write_bytes(b"candidate executable")
    create_unsigned_candidate_manifest(str(source), "1.2.3")
    original = tmp_path / "original-UNSIGNED-RC.zip"
    archive = tmp_path / "tampered-UNSIGNED-RC.zip"
    create_reproducible_zip(str(source), str(original))
    with zipfile.ZipFile(original) as source_zip, zipfile.ZipFile(archive, "w") as tampered_zip:
        for entry in source_zip.infolist():
            contents = source_zip.read(entry.filename)
            if entry.filename == "Aurora/Aurora.exe":
                contents = b"tampered"
            tampered_zip.writestr(entry, contents)

    with pytest.raises(ValueError, match="modified"):
        verify_unsigned_candidate(str(archive))


def test_unsigned_candidate_rejects_source_files(tmp_path):
    source = tmp_path / "Aurora"
    source.mkdir()
    (source / "Aurora.exe").write_bytes(b"candidate executable")
    (source / "developer.py").write_text("private source", encoding="utf-8")
    create_unsigned_candidate_manifest(str(source), "1.2.3")
    archive = tmp_path / "source-UNSIGNED-RC.zip"
    create_reproducible_zip(str(source), str(archive))

    with pytest.raises(ValueError, match="Development source"):
        verify_unsigned_candidate(str(archive))
