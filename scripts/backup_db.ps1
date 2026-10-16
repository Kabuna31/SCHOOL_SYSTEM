param(
    [string]$OutDir = ".\backups"
)

if (-not $env:DATABASE_URL) {
    Write-Error "DATABASE_URL environment variable not set"
    exit 1
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$file = Join-Path $OutDir "school_backup_$stamp.dump"

Write-Host "Backing up to $file ..."
& "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" --format=custom --no-owner --no-privileges --file="$file" $env:DATABASE_URL

$size = "{0:N1} MB" -f ((Get-Item $file).Length / 1MB)
Write-Host "Done. Size: $size"