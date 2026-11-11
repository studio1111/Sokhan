"""Safe audio extraction from media containers using the FFmpeg executable."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


class AudioExtractionError(RuntimeError):
    """Raised when audio extraction cannot be completed safely."""


def extract_audio(
    source: str | Path,
    destination: str | Path,
    *,
    sample_rate: int = 16_000,
    timeout_seconds: float = 600,
) -> Path:
    """Extract mono PCM WAV audio without rendering or modifying the source video."""
    source_path = Path(source)
    destination_path = Path(destination)
    if not source_path.is_file():
        raise FileNotFoundError(f"source media file does not exist: {source_path}")
    if source_path.resolve() == destination_path.resolve():
        raise AudioExtractionError("source and destination must be different files")
    if destination_path.exists():
        raise AudioExtractionError(f"destination already exists: {destination_path}")
    if not destination_path.parent.is_dir():
        raise AudioExtractionError("destination directory does not exist")
    if sample_rate < 8_000 or sample_rate > 96_000:
        raise ValueError("sample_rate must be between 8000 and 96000")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise AudioExtractionError("FFmpeg executable was not found on PATH")

    command = [
        ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-n",
        "-i", str(source_path), "-vn", "-ac", "1", "-ar", str(sample_rate),
        "-c:a", "pcm_s16le", "-f", "wav", str(destination_path),
    ]
    try:
        result = subprocess.run(
            command, check=False, capture_output=True, text=True,
            timeout=timeout_seconds, shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        destination_path.unlink(missing_ok=True)
        raise AudioExtractionError("audio extraction exceeded its time limit") from exc
    except OSError as exc:
        raise AudioExtractionError("FFmpeg could not be started") from exc

    if result.returncode != 0:
        destination_path.unlink(missing_ok=True)
        raise AudioExtractionError("FFmpeg failed to extract an audio stream")
    if not destination_path.is_file() or destination_path.stat().st_size <= 44:
        destination_path.unlink(missing_ok=True)
        raise AudioExtractionError("FFmpeg produced an empty or invalid WAV file")
    return destination_path
