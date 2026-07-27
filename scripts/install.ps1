$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker Desktop is required. Install Docker Desktop and retry.'
}

docker compose version | Out-Null
if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    $secret = -join ((48..57) + (97..102) | Get-Random -Count 64 | ForEach-Object {[char]$_})
    $dbPassword = -join ((48..57) + (97..102) | Get-Random -Count 48 | ForEach-Object {[char]$_})
    $redisPassword = -join ((48..57) + (97..102) | Get-Random -Count 48 | ForEach-Object {[char]$_})
    $envFile = Get-Content '.env'
    $envFile = $envFile -replace '^SECRET_KEY=.*', "SECRET_KEY=$secret"
    $envFile = $envFile -replace '^POSTGRES_PASSWORD=.*', "POSTGRES_PASSWORD=$dbPassword"
    $envFile = $envFile -replace '^REDIS_PASSWORD=.*', "REDIS_PASSWORD=$redisPassword"
    Set-Content '.env' $envFile
    Write-Host 'Created .env with generated local secrets.'
}

New-Item -ItemType Directory -Force -Path backups, logs | Out-Null
docker compose pull
docker compose build
docker compose up -d
& "$PSScriptRoot\verify.ps1"
Write-Host 'Golden Dome SOC is available at http://localhost:8080'
