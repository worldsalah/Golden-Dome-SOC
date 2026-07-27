$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Port = 8080
if (Test-Path '.env') {
    $line = Select-String -Path '.env' -Pattern '^HTTP_PORT=' | Select-Object -First 1
    if ($line) { $Port = $line.Line.Split('=')[1] }
}
$Failed = $false
foreach ($Service in @('db', 'redis', 'ollama', 'backend', 'frontend', 'gateway')) {
    $running = docker compose ps --status running --services | Select-String -SimpleMatch $Service
    if ($running) { Write-Host "PASS  container: $Service" } else { Write-Host "FAIL  container: $Service"; $Failed = $true }
}
foreach ($item in @(@('gateway', "http://localhost:$Port/health"), @('frontend', "http://localhost:$Port/"), @('backend', "http://localhost:$Port/healthz"))) {
    try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 $item[1] | Out-Null; Write-Host "PASS  endpoint: $($item[0])" }
    catch { Write-Host "FAIL  endpoint: $($item[0])"; $Failed = $true }
}
if ($Failed) { exit 1 }
Write-Host 'Verification succeeded.'
