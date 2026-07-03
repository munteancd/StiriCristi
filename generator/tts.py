import asyncio
import concurrent.futures
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


def _ffprobe_duration_seconds(mp3_path: Path, ffmpeg_binary: str) -> float:
    """Extract duration from MP3 using ffmpeg stderr output."""
    try:
        cmd = [ffmpeg_binary, "-i", str(mp3_path)]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        import re
        match = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", proc.stderr)
        if match:
            hours, minutes, seconds = match.groups()
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except Exception as exc:
        log.warning("failed to extract duration for %s: %s", mp3_path, exc)
    return 0.0


# ---------------------------------------------------------------------------
# Edge TTS (Microsoft neural voices, free, requires internet at generation)
# ---------------------------------------------------------------------------

@dataclass
class EdgeTTSConfig:
    # Romanian neural voices: ro-RO-AlinaNeural (female), ro-RO-EmilNeural (male)
    voice: str = "ro-RO-AlinaNeural"
    rate: str = "+0%"    # e.g. "+10%" to speed up slightly
    pitch: str = "+0Hz"
    ffmpeg_binary: str = "ffmpeg"


async def _synthesize_edge_async(
    *, text: str, out_mp3: Path, config: EdgeTTSConfig
) -> float:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError(
            "edge-tts is not installed. Run: pip install edge-tts"
        ) from exc

    out_mp3.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_mp3 = Path(tmpdir) / "raw.mp3"

        communicate = edge_tts.Communicate(
            text,
            voice=config.voice,
            rate=config.rate,
            pitch=config.pitch,
        )
        log.info("edge-tts: generating with voice=%s", config.voice)
        await communicate.save(str(raw_mp3))

        # Re-encode with ffmpeg for consistent bitrate / metadata.
        ffmpeg_cmd = [
            config.ffmpeg_binary,
            "-y",
            "-i", str(raw_mp3),
            "-codec:a", "libmp3lame",
            "-b:a", "96k",
            str(out_mp3),
        ]
        ff = subprocess.run(ffmpeg_cmd, capture_output=True, check=False)
        if ff.returncode != 0:
            raise RuntimeError(
                f"ffmpeg re-encode failed (rc={ff.returncode}): "
                f"{ff.stderr.decode(errors='replace')}"
            )

    return _ffprobe_duration_seconds(out_mp3, config.ffmpeg_binary)


def synthesize_edge(*, text: str, out_mp3: Path, config: EdgeTTSConfig) -> float:
    """Synchronous wrapper around the async edge-tts call.

    Runs in a fresh thread so it never conflicts with an already-running
    event loop (e.g. the one started by asyncio.run(run_pipeline(...))).
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            asyncio.run,
            _synthesize_edge_async(text=text, out_mp3=out_mp3, config=config),
        )
        return future.result()


# ---------------------------------------------------------------------------
# Modal TTS (cloned voice via the xtts-voice app on Modal serverless GPU)
# ---------------------------------------------------------------------------

@dataclass
class ModalTTSConfig:
    # The deployed Modal app/class and the reference voice on its Volume.
    app_name: str = "xtts-voice"
    cls_name: str = "XTTS"
    speaker: str = "cristi"     # reference sample voci/<speaker>.wav on the Volume
    language: str = "ro"
    temperature: float = 0.85   # validated profile (multi-clip ref + speed 1.35 in the app)
    ffmpeg_binary: str = "ffmpeg"


def synthesize_modal(*, text: str, out_mp3: Path, config: ModalTTSConfig) -> float:
    """Generate an MP3 in the cloned voice via the Modal xtts-voice app.

    Calls the deployed XTTS class remotely, which returns 24 kHz WAV bytes,
    then re-encodes to MP3 at 96k to match the edge-tts output. Requires the
    `modal` client and MODAL_TOKEN_ID / MODAL_TOKEN_SECRET in the environment.
    """
    import modal

    out_mp3.parent.mkdir(parents=True, exist_ok=True)

    xtts = modal.Cls.from_name(config.app_name, config.cls_name)()
    log.info("modal-tts: synthesizing with speaker=%s temp=%s",
             config.speaker, config.temperature)
    wav_bytes: bytes = xtts.synthesize.remote(
        text, config.language, config.speaker, config.temperature
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_wav = Path(tmpdir) / "raw.wav"
        raw_wav.write_bytes(wav_bytes)

        ffmpeg_cmd = [
            config.ffmpeg_binary,
            "-y",
            "-i", str(raw_wav),
            "-codec:a", "libmp3lame",
            "-b:a", "96k",
            str(out_mp3),
        ]
        ff = subprocess.run(ffmpeg_cmd, capture_output=True, check=False)
        if ff.returncode != 0:
            raise RuntimeError(
                f"ffmpeg re-encode failed (rc={ff.returncode}): "
                f"{ff.stderr.decode(errors='replace')}"
            )

    return _ffprobe_duration_seconds(out_mp3, config.ffmpeg_binary)


# ---------------------------------------------------------------------------
# Edge + RVC (Emil prosody converted to Cristi's timbre on Modal)
# ---------------------------------------------------------------------------

@dataclass
class EdgeRVCConfig:
    """Edge-TTS provides native Romanian prosody (rhythm, diction, number
    reading); the RVC model on Modal swaps only the timbre, preserving timing
    1:1. This replaced the XTTS clone, which sounded choppy."""
    voice: str = "ro-RO-EmilNeural"
    rate: str = "-4%"           # validated pace (~2.3 words/sec)
    rvc_app: str = "rvc"        # deployed Modal app with the trained model
    rvc_function: str = "convert"
    transpose: int = 0          # 0 for male source → male target
    ffmpeg_binary: str = "ffmpeg"


def synthesize_edge_rvc(*, text: str, out_mp3: Path, config: EdgeRVCConfig) -> float:
    """Generate Emil audio with edge-tts, then convert it to Cristi's timbre
    via the Modal `rvc` app. Requires MODAL_TOKEN_ID / MODAL_TOKEN_SECRET.
    """
    import modal

    out_mp3.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        edge_mp3 = Path(tmpdir) / "edge.mp3"
        edge_seconds = synthesize_edge(
            text=text,
            out_mp3=edge_mp3,
            config=EdgeTTSConfig(
                voice=config.voice,
                rate=config.rate,
                ffmpeg_binary=config.ffmpeg_binary,
            ),
        )

        # The RVC model expects 40 kHz mono WAV input.
        wav_40k = Path(tmpdir) / "edge_40k.wav"
        ff = subprocess.run(
            [config.ffmpeg_binary, "-y", "-i", str(edge_mp3),
             "-ar", "40000", "-ac", "1", str(wav_40k)],
            capture_output=True, check=False,
        )
        if ff.returncode != 0:
            raise RuntimeError(
                f"ffmpeg 40k resample failed (rc={ff.returncode}): "
                f"{ff.stderr.decode(errors='replace')}"
            )

        convert = modal.Function.from_name(config.rvc_app, config.rvc_function)
        log.info("edge-rvc: converting %.0fs of %s audio to Cristi's timbre",
                 edge_seconds, config.voice)
        converted: bytes = convert.remote(wav_40k.read_bytes(), config.transpose)

        conv_wav = Path(tmpdir) / "converted.wav"
        conv_wav.write_bytes(converted)

        ff = subprocess.run(
            [config.ffmpeg_binary, "-y", "-i", str(conv_wav),
             "-codec:a", "libmp3lame", "-b:a", "96k", str(out_mp3)],
            capture_output=True, check=False,
        )
        if ff.returncode != 0:
            raise RuntimeError(
                f"ffmpeg re-encode failed (rc={ff.returncode}): "
                f"{ff.stderr.decode(errors='replace')}"
            )

    duration = _ffprobe_duration_seconds(out_mp3, config.ffmpeg_binary)
    # RVC preserves timing 1:1 — a large drift means truncated/corrupt output,
    # so fail the voice (the pipeline isolates it and still ships the others).
    if edge_seconds and abs(duration - edge_seconds) > max(2.0, edge_seconds * 0.05):
        raise RuntimeError(
            f"edge-rvc duration drift: edge={edge_seconds:.1f}s "
            f"converted={duration:.1f}s"
        )
    return duration


# ---------------------------------------------------------------------------
# Unified voice registry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VoiceSpec:
    """A named TTS voice that the pipeline can generate audio for."""
    id: str          # short slug used in filenames, e.g. "alina", "emil"
    label: str       # display name shown in the UI
    gender: str      # "male" | "female"
    backend: str     # "edge" | "modal" | "edge_rvc"
    config: "EdgeTTSConfig | ModalTTSConfig | EdgeRVCConfig"


# Built-in voices — subset is enabled per-run via sources.yaml or env config.
AVAILABLE_VOICES: list[VoiceSpec] = [
    VoiceSpec(
        id="alina",
        label="Alina",
        gender="female",
        backend="edge",
        config=EdgeTTSConfig(voice="ro-RO-AlinaNeural"),
    ),
    VoiceSpec(
        id="emil",
        label="Emil",
        gender="male",
        backend="edge",
        config=EdgeTTSConfig(voice="ro-RO-EmilNeural"),
    ),
    # Cristi's voice: Emil prosody + RVC timbre conversion on Modal. If Modal
    # is unavailable at generation time, the pipeline isolates the failure and
    # still ships Alina + Emil, so the site never breaks.
    VoiceSpec(
        id="cristi",
        label="Cristi",
        gender="male",
        backend="edge_rvc",
        config=EdgeRVCConfig(),
    ),
]

VOICE_BY_ID: dict[str, VoiceSpec] = {v.id: v for v in AVAILABLE_VOICES}


def synthesize_voice(*, text: str, out_mp3: Path, voice: VoiceSpec) -> float:
    """Generate an MP3 for the given voice spec. Returns duration in seconds.

    Neural voices handle foreign words natively, so they receive the original
    text unchanged.
    """
    if voice.backend == "edge":
        assert isinstance(voice.config, EdgeTTSConfig)
        return synthesize_edge(text=text, out_mp3=out_mp3, config=voice.config)
    elif voice.backend == "modal":
        assert isinstance(voice.config, ModalTTSConfig)
        return synthesize_modal(text=text, out_mp3=out_mp3, config=voice.config)
    elif voice.backend == "edge_rvc":
        assert isinstance(voice.config, EdgeRVCConfig)
        return synthesize_edge_rvc(text=text, out_mp3=out_mp3, config=voice.config)
    else:
        raise ValueError(f"Unknown TTS backend: {voice.backend!r}")
