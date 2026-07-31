#Requires -RunAsAdministrator
# Golden Dome SOC — Windows Installer (uses WSL2)
param(
    [string]$Distro = "Ubuntu-24.04",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

function Get-ServerIp {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.IPAddress -notmatch '^127' -and $_.IPAddress -notmatch '^169\.254' -and $_.PrefixOrigin -ne 'WellKnown'
    } | Select-Object -First 1).IPAddress
    if (-not $ip) {
        $ip = (Test-Connection -ComputerName (hostname) -Count 1 -ErrorAction SilentlyContinue).Address
    }
    if (-not $ip) { $ip = "SERVER_IP" }
    return $ip
}

function Write-Ok($msg) { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

$ip = Get-ServerIp
Write-Step "Golden Dome SOC Windows Installer"
Write-Host "Detected server IP: $ip"

# Check WSL
Write-Step "Checking WSL2..."
$wslStatus = wsl --status 2>&1
if ($LASTEXITCODE -ne 0 -or $wslStatus -match "WSL is not installed" -or $wslStatus -match "WSL is not deregistered") {
    Write-Host "WSL2 is not installed. Enabling WSL2 and installing $Distro..." -ForegroundColor Yellow
    wsl --install -d $Distro
    Write-Host "`nA reboot is required to finish WSL setup." -ForegroundColor Yellow
    Write-Host "After reboot, run this script again to deploy Golden Dome." -ForegroundColor Yellow
    exit 0
}

$distros = wsl -l -v 2>&1
if ($distros -notmatch [regex]::Escape($Distro)) {
    Write-Step "Installing $Distro..."
    wsl --install -d $Distro
    Write-Host "Reboot, then re-run this script." -ForegroundColor Yellow
    exit 0
}

Write-Ok "WSL2 and $Distro are available"

# Run the Linux installer inside WSL as root
$installCmd = "apt-get update && apt-get install -y curl git && curl -fsSL https://raw.githubusercontent.com/worldsalah/Golden-Dome-SOC/$Branch/install.sh | bash"
Write-Step "Deploying Golden Dome inside WSL..."
$proc = Start-Process -FilePath "wsl" -ArgumentList "-d $Distro -u root -e bash -c `"$installCmd`"" -NoNewWindow -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    throw "Golden Dome deployment failed. Exit code: $($proc.ExitCode)"
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "  Golden Dome deployed successfully." -ForegroundColor Green
Write-Host "  Access: https://$ip" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
