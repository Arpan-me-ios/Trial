import os
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro

from scripts.env_loader import load_local_env


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "kokoro-v1.0.onnx"
VOICES_PATH = PROJECT_ROOT / "models" / "voices-v1.0.bin"
TEMP_DIR = PROJECT_ROOT / ".tmp"


def _prepare_runtime_temp() -> None:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["TMP"] = str(TEMP_DIR)
    os.environ["TEMP"] = str(TEMP_DIR)
    os.environ["TMPDIR"] = str(TEMP_DIR)


def _require_kokoro_files() -> None:
    load_local_env()
    if not MODEL_PATH.exists() or not VOICES_PATH.exists():
        try:
            from scripts.model_downloader import ensure_kokoro_models

            ensure_kokoro_models()
        except Exception as exc:
            if os.getenv("YT_PIPELINE_STRICT_KOKORO_DOWNLOAD", "0") == "1":
                raise
            download_error = exc
        else:
            download_error = None
    else:
        download_error = None

    missing = []
    if not os.path.exists(MODEL_PATH):
        missing.append(str(MODEL_PATH))
    if not os.path.exists(VOICES_PATH):
        missing.append(str(VOICES_PATH))
    if missing:
        raise FileNotFoundError(
            "Kokoro-ONNX model assets are missing. Download or place the exact local files before "
            "running TTS. Expected files: "
            f"model={MODEL_PATH}, voices={VOICES_PATH}. Missing: {missing}. "
            "The pipeline intentionally does not download weights at runtime so automation remains "
            "predictable unless KOKORO_MODEL_URL and KOKORO_VOICES_URL are configured. "
            f"Automatic download attempt result: {download_error}"
        )


def generate_voiceover(text_script: str, output_path: str, voice: str = "af_sarah") -> str:
    text = " ".join(text_script.split())
    if not text:
        raise ValueError("text_script is empty; cannot synthesize a voiceover.")
    if not output_path.lower().endswith(".wav"):
        raise ValueError("output_path must end with .wav for a clean PCM voiceover track.")

    _require_kokoro_files()
    _prepare_runtime_temp()
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
    samples, sample_rate = kokoro.create(text, voice=voice)
    sf.write(str(destination), samples, sample_rate)
    return str(destination)
