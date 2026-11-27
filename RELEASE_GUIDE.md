# Aurora portable release guide

This workflow creates a Windows x64 portable ZIP. The repository is the private developer/build repository; only the explicitly staged `Aurora/` directory is distributed. Users receive compiled executables, the standalone runtime, approved frontend files, application assets and user-facing documentation—not Git history, tests, credentials or Python source files.

## Current validation snapshot — 2026-11-27

- PyInstaller ONEDIR v10 build and frozen `--self-check` passed. Frozen server smoke passed health/database, frontend HTTP 200, native FastAPI WebSocket, local Ollama/model detection, missing-model rejection, RAG ingestion/retrieval, graceful shutdown, restart, and RAG persistence.
- Full backend suite: 120 passed, with three upstream deprecation/future warnings.
- No portable ZIP or unsigned candidate has been generated. The checkout still has uncommitted changes, so the packager's dirty-checkout gate must reject packaging.
- Official signing is BLOCKED because no authorized external key pair or independently published fingerprint was supplied. Clean Windows VM, updater/rollback, full offline, voice/FFmpeg, and outbound-traffic observation remain untested.
- See [PORTABLE_RELEASE_CHECKLIST.md](./PORTABLE_RELEASE_CHECKLIST.md) and [RELEASE_VALIDATION_REPORT.md](./RELEASE_VALIDATION_REPORT.md) for command output, warning dispositions, and the complete changed-path inventory.

## Release prerequisites

- Windows 10/11 x64 build host, Python 3.12 x64, Node.js 20, Git and the project dependencies.
- `backend/requirements.txt` pins `transformers==4.44.2`; keep that pin unless a replacement passes the frozen RAG tests. The PyInstaller build is ONEDIR and must not be switched to Nuitka.
- A protected signing key held outside the repository. Never put the private key in the checkout, ZIP, CI logs or user data.
- The public-key SHA-256 fingerprint published through an independent official channel.
- For GitHub publishing: configure the `aurora-release` environment with an authorized reviewer, `AURORA_RELEASE_PRIVATE_KEY` and `AURORA_RELEASE_PUBLIC_KEY` secrets, and `AURORA_RELEASE_KEY_FINGERPRINT` as a variable. Only authorized maintainers should be allowed to approve that environment and push release tags.

Create the Ed25519 key pair on a trusted offline machine and retain the private key there:

```powershell
openssl genpkey -algorithm ED25519 -out C:\AuroraKeys\aurora-release-private.pem
openssl pkey -in C:\AuroraKeys\aurora-release-private.pem -pubout -out C:\AuroraKeys\aurora-release-public.pem
```

Compute the fingerprint of the **raw** Ed25519 public key (not the PEM file):

```powershell
python -c "import hashlib; from cryptography.hazmat.primitives import serialization; p=serialization.load_pem_public_key(open(r'C:\AuroraKeys\aurora-release-public.pem','rb').read()); print(hashlib.sha256(p.public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)).hexdigest())"
```

Verify the fingerprint independently before publishing it. Keep private-key backups offline and access-controlled. If the key is compromised, stop publishing, distribute a new trusted fingerprint through the independent channel, and treat old-key updates as untrusted.

## Build and package locally

1. Update `packaging/portable/VERSION` and add release notes to `packaging/portable/CHANGELOG.md`. Use `MAJOR.MINOR.PATCH`; the release tag must be `v` followed by that same version.
2. Commit the reviewed source changes and ensure the Git worktree has no staged, unstaged or untracked changes; package signing intentionally refuses a dirty checkout.
3. Run the full backend suite and review the source, dependencies, frontend output and changelog.
4. Build the production frontend and Windows bundle from the repository root. The script installs backend and packaging requirements, runs `npm ci`, lint, and the frontend production build, then runs the PyInstaller ONEDIR build and creates the verifier and launcher executables:

   ```powershell
   .\packaging\portable\build_release.ps1
   ```

   If `frontend/dist` is already a verified production build, use a unique output directory and skip only the frontend commands:

   ```powershell
   $buildRoot = Join-Path $env:TEMP ("Aurora-release-build-" + [guid]::NewGuid().ToString('N'))
   .\packaging\portable\build_release.ps1 -SkipFrontendBuild -OutputRoot $buildRoot
   ```

### Unsigned engineering candidate

An unsigned candidate is for internal engineering validation only. It is not an official release, must not be published as trusted, and must not be installed by the updater. The normal dirty-checkout gate remains enabled. Use new, non-existing output directories outside the repository:

```powershell
$buildRoot = Join-Path $env:TEMP ("Aurora-build-" + [guid]::NewGuid().ToString('N'))
.\packaging\portable\build_release.ps1 -OutputRoot $buildRoot

$candidateRoot = Join-Path $env:TEMP ("Aurora-UNSIGNED-RC-" + [guid]::NewGuid().ToString('N'))
.\packaging\portable\package_portable.ps1 `
  -UnsignedCandidate `
  -OutputRoot $candidateRoot `
  -DistributionPath (Join-Path $buildRoot 'portable-dist\Aurora') `
  -ToolsDirectory (Join-Path $buildRoot 'portable-tools')
```

The package script labels the filename, README and manifest `UNSIGNED-RC`, generates SHA-256 values, checks ZIP CRC and rejects source, bytecode, databases, `.env` files and Git metadata. This integrity-only check does not authenticate a publisher. Extract to a new short path and inspect the complete layout before running the executable. Do not pass an unsigned candidate to `Update-Aurora.ps1` or `Test-PortableRelease.ps1`; both require the official signature-verification path.

### Official signed package

5. Package and sign an official release only after the clean checkout and release prerequisites are satisfied. Set these variables only in the current process, with key files outside the checkout:

    ```powershell
    $env:AURORA_RELEASE_PRIVATE_KEY = 'C:\AuroraKeys\aurora-release-private.pem'
    $env:AURORA_RELEASE_PUBLIC_KEY = 'C:\AuroraKeys\aurora-release-public.pem'
    $env:AURORA_RELEASE_KEY_FINGERPRINT = '<independently-published-64-hex-fingerprint>'
    .\packaging\portable\package_portable.ps1
    ```

   The build produces `release\Aurora-v<version>-Windows-x64-Portable.zip` and a `.sha256` sidecar. The archive has a single `Aurora/` root with `Aurora.exe`, `Start Aurora.exe`, `runtime/`, `resources/`, `frontend/`, `scripts/`, `README.txt`, `LICENSE.txt`, `VERSION`, `CHANGELOG.md`, `SHA256SUMS.txt` and the signed release manifest. Members are sorted and use normalized ZIP timestamps; packaging the same signed staging tree with the same Python/zlib version produces identical ZIP bytes. Existing staging folders, ZIPs and checksum files are never silently overwritten.

6. Verify the archive using the independent fingerprint and public key:

   ```powershell
   .\packaging\portable\verify_release.ps1 `
     -Zip .\release\Aurora-v1.0.0-Windows-x64-Portable.zip `
     -PublicKey C:\AuroraKeys\aurora-release-public.pem `
     -Fingerprint '<independently-published-64-hex-fingerprint>'
   ```

7. Inspect the archive contents for unexpected files and run this from a clean Windows 10/11 x64 VM, with an independently obtained trusted verifier and public key. Choose a new `WorkDir` that does not already exist:

   ```powershell
   .\Test-PortableRelease.ps1 `
     -ZipPath .\Aurora-v1.0.0-Windows-x64-Portable.zip `
     -TrustedFingerprint '<independently-published-64-hex-fingerprint>' `
     -VerifierExe C:\Trusted\AuroraReleaseVerifier.exe `
     -PublicKeyPath C:\Trusted\release_public_key.pem `
     -ObserveSeconds 120 `
     -WorkDir C:\aurora-validation-new
   ```

   Record manual checks as well as automated checks. Do not publish if any required check fails or remains unverified.

## Publish through GitHub Actions

After local review and VM validation, commit the approved source changes and push the matching `vMAJOR.MINOR.PATCH` tag. The release workflow builds the signed ZIP inside the protected `aurora-release` environment and publishes it as a GitHub Release asset. Require authorized environment approval; do not make a release tag trigger an unreviewed deployment. Confirm the attached ZIP and checksum, then independently verify the published file before announcing it.

The workflow is a publication mechanism, not proof of release quality. Keep a clean-VM validation record for each released artifact.

## Build technology and reproducibility

The current release build uses the checked-in PyInstaller ONEDIR specification because that is the packaging path already exercised in this repository. `nuitka-project.py` provides a Nuitka standalone project entry point, but is not the release workflow's compiler until the full app and native dependency set pass the same clean-machine acceptance matrix. Do not describe the current output as a Nuitka build.

The build manifest records semantic version, build timestamp, release identifier, architecture, release notes, signing-key fingerprint and per-file SHA-256 hashes. ZIP packaging is deterministic for the same signed stage and toolchain. The PyInstaller executable build itself is not asserted to be bit-for-bit reproducible; the signed file hashes and release identifier provide payload provenance and integrity.

The dependency audit found no Aurora source imports of `einops`, TensorBoard, TensorFlow, Socket.IO, or LangChain; these remain excluded/not required. The Windows Torch runtime imports `torch.distributed` through `torch.utils.data.dataloader`, so the core namespace must not be excluded. A frozen RAG failure also showed that `torch.testing` is imported by Torch autograd during model initialization, so the spec retains that runtime module while still excluding test trees. Do not set `KMP_DUPLICATE_LIB_OK`; it is not a supported release workaround.

## User updates and recovery

Updates are optional and user-initiated. From the extracted application directory, use the commands below only with an official signed ZIP and a fingerprint obtained independently:

```powershell
.\scripts\Update-Aurora.ps1 -Fingerprint '<independently-published-64-hex-fingerprint>'
# Offline import uses the same signature verification:
.\scripts\Update-Aurora.ps1 -PackagePath C:\Downloads\Aurora-v1.0.0-Windows-x64-Portable.zip `
  -Fingerprint '<independently-published-64-hex-fingerprint>'
# After an update failure, give the previous application backup path printed by the updater:
.\scripts\Rollback-Aurora.ps1 -BackupPath "$env:LOCALAPPDATA\Aurora\backups\portable-app-<timestamp>"
```

The updater checks only the official Aurora GitHub Releases endpoint, or accepts an offline ZIP via `-PackagePath`. It verifies the signature and hashes before extraction, displays the signed release notes, requires explicit confirmation, backs up the old application and performs an application self-check. Data remains in `%LOCALAPPDATA%\Aurora` and is not copied over by application updates. `Backup-AuroraData.ps1` and `Restore-AuroraData.ps1` are separate user-controlled data operations.

The user must supply the independently obtained release fingerprint. A public key shipped in the package is not trusted by itself; the fingerprint anchors publisher identity. Offline installs do not perform automatic network checks and may import only a ZIP that passes the same signature verification.

## Validation boundary

The build host is not a clean target machine. A release must still be extracted and run on a clean Windows 10/11 x64 VM with no Python, Node.js or developer tools. The automated test checks the signature, tampering, ZIP layout, launch/self-check, HTTP health, frontend response, loopback binding, user data directories and observed outbound connections. Manually record: FastAPI chat and native WebSocket behavior (this code uses FastAPI WebSockets; it does not expose a Socket.IO endpoint), Ollama missing/present, model missing/present, FAISS/RAG ingestion and retrieval, voice/FFmpeg paths where applicable, persistence across restart/update, update confirmation and data preservation, failed-update rollback, backup/restore, offline operation with cached models, and no cloud AI/telemetry. This repository cannot claim those tests passed until a maintainer records the VM results.
