# Text Anonymizer - one-click installer for Windows (PowerShell).
# Easiest: double-click install-windows.bat (it runs this script).
# It installs Docker if needed, downloads and starts the service, and opens the UI.

$Image = "ghcr.io/levaraorg/text-anonymizer:latest"
$Name  = "text-anonymizer"
$Port  = 8000
$Url   = "http://localhost:$Port/"

Write-Host "================================================"
Write-Host "  Text Anonymizer - Installation (Windows)"
Write-Host "================================================"
Write-Host ""

function Test-DockerUp { try { docker info *> $null; return ($LASTEXITCODE -eq 0) } catch { return $false } }
function Pause-Exit($code) { Write-Host ""; Read-Host "Enter zum Beenden" | Out-Null; exit $code }

# 1) Is Docker installed?
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Host "Docker ist nicht installiert."
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "Installiere Docker Desktop ueber winget (kann einige Minuten dauern)..."
    winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
    Write-Host ""
    Write-Host "Docker Desktop wurde installiert. Bitte Windows ggf. neu starten,"
    Write-Host "Docker Desktop einmal oeffnen und dieses Skript dann erneut ausfuehren."
    Pause-Exit 1
  } else {
    Start-Process "https://www.docker.com/products/docker-desktop/"
    Write-Host "Bitte Docker Desktop installieren und Skript erneut ausfuehren."
    Pause-Exit 1
  }
}

# 2) Is the Docker daemon running?
if (-not (Test-DockerUp)) {
  Write-Host "Starte Docker Desktop..."
  $dd = Join-Path $Env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
  if (Test-Path $dd) { Start-Process $dd }
  Write-Host -NoNewline "Warte, bis Docker bereit ist"
  for ($i = 0; $i -lt 60; $i++) {
    if (Test-DockerUp) { Write-Host " - bereit."; break }
    Write-Host -NoNewline "."; Start-Sleep -Seconds 2
  }
  if (-not (Test-DockerUp)) {
    Write-Host ""
    Write-Host "Docker ist nicht gestartet. Bitte Docker Desktop oeffnen und Skript erneut ausfuehren."
    Pause-Exit 1
  }
}

# 3) Pull the image
Write-Host "Lade das Programm herunter..."
docker pull $Image
if ($LASTEXITCODE -ne 0) { Write-Host "Download fehlgeschlagen."; Pause-Exit 1 }

# 4) (Re)start the container
docker rm -f $Name *> $null
Write-Host "Starte den Dienst..."
docker run -d --name $Name -p "$($Port):8000" -v text-anonymizer-models:/root/.cache/huggingface --restart unless-stopped $Image | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "Start fehlgeschlagen (Port $Port belegt?)."; Pause-Exit 1 }

# 5) Wait for health
Write-Host -NoNewline "Warte, bis der Dienst bereit ist"
for ($i = 0; $i -lt 30; $i++) {
  try { Invoke-WebRequest -UseBasicParsing "http://localhost:$Port/health" -TimeoutSec 2 *> $null; Write-Host " - bereit."; break }
  catch { Write-Host -NoNewline "."; Start-Sleep -Seconds 1 }
}

Write-Host ""
Write-Host "Fertig! Die Oberflaeche oeffnet sich im Browser:"
Write-Host "  $Url"
Start-Process $Url
Write-Host ""
Write-Host "Nuetzlich:  docker stop $Name   (stoppen)"
Write-Host "            docker start $Name  (wieder starten)"
Write-Host "            docker rm -f $Name  (entfernen)"
Pause-Exit 0
