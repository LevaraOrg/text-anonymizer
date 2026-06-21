#!/usr/bin/env bash
#
# Text Anonymizer – one-click installer for macOS.
# Double-click this file in Finder, or run it in Terminal.
# It installs Docker if needed, downloads and starts the service, and opens the UI.
#
set -uo pipefail

IMAGE="ghcr.io/levaraorg/text-anonymizer:latest"
NAME="text-anonymizer"
PORT=8000
URL="http://localhost:${PORT}/"

echo "================================================"
echo "  Text Anonymizer – Installation (macOS)"
echo "================================================"
echo

pause_exit() { echo; read -r -p "Drücke Enter zum Beenden…" _; exit "${1:-0}"; }

# 1) Is Docker installed?
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker ist nicht installiert."
  if command -v brew >/dev/null 2>&1; then
    echo "Installiere Docker Desktop über Homebrew (kann einige Minuten dauern)…"
    brew install --cask docker || { echo "Installation fehlgeschlagen."; pause_exit 1; }
  else
    echo "Bitte Docker Desktop installieren: https://www.docker.com/products/docker-desktop/"
    open "https://www.docker.com/products/docker-desktop/" 2>/dev/null || true
    echo "Danach dieses Skript erneut ausführen."
    pause_exit 1
  fi
fi

# 2) Is the Docker daemon running?
if ! docker info >/dev/null 2>&1; then
  echo "Starte Docker Desktop…"
  open -a Docker 2>/dev/null || true
  printf "Warte, bis Docker bereit ist"
  for _ in $(seq 1 60); do
    docker info >/dev/null 2>&1 && { echo " – bereit."; break; }
    printf "."; sleep 2
  done
  if ! docker info >/dev/null 2>&1; then
    echo; echo "Docker ist nicht gestartet. Bitte Docker Desktop manuell öffnen und Skript erneut ausführen."
    pause_exit 1
  fi
fi

# 3) Pull the image
echo "Lade das Programm herunter…"
docker pull "$IMAGE" || { echo "Download fehlgeschlagen."; pause_exit 1; }

# 4) (Re)start the container
docker rm -f "$NAME" >/dev/null 2>&1 || true
echo "Starte den Dienst…"
docker run -d --name "$NAME" -p "${PORT}:8000" \
  -v text-anonymizer-models:/root/.cache/huggingface \
  --restart unless-stopped "$IMAGE" >/dev/null || { echo "Start fehlgeschlagen (Port ${PORT} belegt?)."; pause_exit 1; }

# 5) Wait for health
printf "Warte, bis der Dienst bereit ist"
for _ in $(seq 1 30); do
  curl -fs "http://localhost:${PORT}/health" >/dev/null 2>&1 && { echo " – bereit."; break; }
  printf "."; sleep 1
done

echo
echo "Fertig! Die Oberfläche öffnet sich im Browser:"
echo "  $URL"
open "$URL" 2>/dev/null || true
echo
echo "Nützlich:  docker stop $NAME   (stoppen)"
echo "           docker start $NAME  (wieder starten)"
echo "           docker rm -f $NAME  (entfernen)"
pause_exit 0
