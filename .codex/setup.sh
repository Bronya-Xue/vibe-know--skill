#!/usr/bin/env bash
# Codex cloud setup script; run from any directory.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

admin=()
if [[ "$(id -u)" != 0 ]]; then
  if command -v sudo >/dev/null && sudo -n true 2>/dev/null; then
    admin=(sudo -n)
  fi
fi

if ! command -v ffmpeg >/dev/null || ! command -v ffprobe >/dev/null; then
  if [[ "$(id -u)" != 0 && ${#admin[@]} == 0 ]]; then
    echo 'Install ffmpeg (including ffprobe) in the base image, or run setup with sudo.' >&2
    exit 1
  fi
  "${admin[@]}" apt-get update
  "${admin[@]}" apt-get install -y --no-install-recommends ffmpeg
fi

python3 -m pip install -r requirements.txt

if [[ -n "${VK_BROWSER_EXECUTABLE:-}" ]]; then
  test -x "$VK_BROWSER_EXECUTABLE"
elif command -v google-chrome >/dev/null || command -v google-chrome-stable >/dev/null || command -v chromium >/dev/null || command -v chromium-browser >/dev/null; then
  echo 'Using the Chrome/Chromium already installed in the image.'
else
  if [[ "$(id -u)" == 0 || ${#admin[@]} != 0 ]]; then
    "${admin[@]}" "$(command -v python3)" -m playwright install-deps chromium
  fi
  python3 -m playwright install chromium
fi

python3 engine/get_fonts.py
python3 engine/get_fonts.py --check
python3 .codex/check.py
