#!/usr/bin/env bash
# Downloads Piper Romanian voice models used by the generator.
# Run once locally, and in the GitHub Actions workflow (cached).
#
# Available TTS backends:
#   - Piper (offline): ro_RO-mihai-medium (male) — downloaded here
#   - Edge TTS (online, no download needed):
#       ro-RO-AlinaNeural (female), ro-RO-EmilNeural (male)
#     Enable via: TTS_VOICES=mihai,alina or --voices mihai,alina
set -euo pipefail

VOICE_DIR="${VOICE_DIR:-generator/voices}"
mkdir -p "$VOICE_DIR"

VOICE="ro_RO-mihai-medium"
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/ro/ro_RO/mihai/medium"

curl -L -o "$VOICE_DIR/${VOICE}.onnx"       "${BASE}/${VOICE}.onnx"
curl -L -o "$VOICE_DIR/${VOICE}.onnx.json"  "${BASE}/${VOICE}.onnx.json"

echo "Downloaded $VOICE to $VOICE_DIR"
echo ""
echo "Edge TTS voices (no download needed, require internet at generation time):"
echo "  ro-RO-AlinaNeural  (female)"
echo "  ro-RO-EmilNeural   (male)"
echo ""
echo "To generate with multiple voices, set TTS_VOICES=mihai,alina in .env"
