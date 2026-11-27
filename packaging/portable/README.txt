Aurora Portable for Windows x64

This package supports Windows 10/11 x64 only. Extract the Aurora folder to a writable location and run Start Aurora.exe. Aurora.exe is also available for direct launch. Python and developer tools are not required. Do not move or delete the runtime folder. No administrator rights are needed.

Aurora stores personal data in %LOCALAPPDATA%\Aurora\config, database, conversations, faiss_index, documents, and logs. Updates do not replace this user data. Aurora binds its local API to 127.0.0.1.

Local AI setup: install Ollama from https://ollama.com/download, start it, and download the configured model (default: ollama run llama3.2:3b). Aurora does not include Ollama or AI models. Ollama model downloads require internet; inference uses the local Ollama service. Optional voice and document-embedding features may also fetch their model weights on first use; fully offline use requires those weights to be cached beforehand. The launcher checks for Ollama and the configured model and shows setup steps when either is missing. Change the model in %LOCALAPPDATA%\Aurora\config\aurora.env.

To check for an update, open PowerShell in this folder and run scripts\Update-Aurora.ps1 -Fingerprint <developer-published-fingerprint>. The checker only checks the official Aurora GitHub Releases page. To update offline, pass a release ZIP with -PackagePath. The updater verifies the signature and checksums, displays release notes, asks for confirmation, and keeps the previous application in %LOCALAPPDATA%\Aurora\backups. Never run an unsigned or unverified update. The signing-key fingerprint must be obtained independently from the official Aurora developer channel.

Back up and restore user data with scripts\Backup-AuroraData.ps1 and scripts\Restore-AuroraData.ps1. To restore an earlier app version, run scripts\Rollback-Aurora.ps1 and provide the previous application backup path. Application rollback does not overwrite your user data.

This is a proprietary distribution. Compiling the application does not make its code or resources impossible to inspect or recover. Verify release_manifest.json and SHA256SUMS.txt with scripts\Verify-Release.ps1 before installing an imported ZIP. Linux and macOS require separate builds.
