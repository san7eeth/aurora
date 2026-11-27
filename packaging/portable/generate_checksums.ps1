param([Parameter(Mandatory=$true)][string]$Path)
$ErrorActionPreference='Stop'
$item=Get-Item -LiteralPath $Path
if ($item.PSIsContainer) { $files=Get-ChildItem -LiteralPath $item.FullName -File -Recurse | Where-Object Name -ne 'SHA256SUMS.txt'; $base=$item.FullName }
else { $files=@($item); $base=$item.DirectoryName }
$lines=foreach($file in $files) { $relative=$file.FullName.Substring($base.Length).TrimStart('\','/').Replace('\','/'); "$( (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToLower() )  $relative" }
$lines | Set-Content -LiteralPath (Join-Path $base 'SHA256SUMS.txt') -Encoding ascii
