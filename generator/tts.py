import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class PiperConfig:
    voice_id: str = "ro_RO-mihai-medium"
    voice_dir: Path = field(default_factory=lambda: Path("generator/voices"))
    piper_binary: str = "piper"  # Assumes piper is in PATH or current dir
    ffmpeg_binary: str = "ffmpeg" # Assumes ffmpeg is in PATH


def _ffprobe_duration_seconds(mp3_path: Path, ffmpeg_binary: str) -> float:
    """Extract duration from MP3 using ffmpeg output parsing."""
    try:
        cmd = [ffmpeg_binary, "-i", str(mp3_path)]
        # ffmpeg outputs info to stderr
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = proc.stderr
        
        # Look for "Duration: 00:01:42.50"
        import re
        match = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", output)
        if match:
            hours, minutes, seconds = match.groups()
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except Exception as exc:
        log.warning("failed to extract duration for %s: %s", mp3_path, exc)
    
    return 0.0


def synthesize(*, text: str, out_mp3: Path, config: PiperConfig) -> float:
    model_path = config.voice_dir / f"{config.voice_id}.onnx"
    model_json = config.voice_dir / f"{config.voice_id}.onnx.json"
    if not model_path.exists() or not model_json.exists():
        raise FileNotFoundError(
            f"Piper voice model not found at {model_path}. "
            "Run scripts/download_voice.sh or pass voice_dir."
        )

    out_mp3.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "out.wav"

        piper_cmd = [
            config.piper_binary,
            "--model", str(model_path),
            "--output_file", str(wav_path),
        ]
        log.info("running piper: %s", piper_cmd)
        piper = subprocess.run(
            piper_cmd,
            input=text.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        if piper.returncode != 0:
            raise RuntimeError(
                f"piper failed (rc={piper.returncode}): {piper.stderr.decode(errors='replace')}"
            )

        ffmpeg_cmd = [
            config.ffmpeg_binary,
            "-y",
            "-i", str(wav_path),
            "-codec:a", "libmp3lame",
            "-b:a", "96k",
            str(out_mp3),
        ]
        log.info("running ffmpeg: %s", ffmpeg_cmd)
        ff = subprocess.run(ffmpeg_cmd, capture_output=True, check=False)
        if ff.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed (rc={ff.returncode}): {ff.stderr.decode(errors='replace')}"
            )

    return _ffprobe_duration_seconds(out_mp3, config.ffmpeg_binary)
