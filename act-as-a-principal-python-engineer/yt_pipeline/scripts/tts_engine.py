import os
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "kokoro-v1.0.onnx"
VOICES_PATH = PROJECT_ROOT / "models" / "voices-v1.0.bin"


def _require_kokoro_files() -> None:
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
            "predictable and fully local."
        )


def generate_voiceover(text_script: str, output_path: str, voice: str = "af_sarah") -> str:
    text = " ".join(text_script.split())
    if not text:
        raise ValueError("text_script is empty; cannot synthesize a voiceover.")
    if not output_path.lower().endswith(".wav"):
        raise ValueError("output_path must end with .wav for a clean PCM voiceover track.")

    _require_kokoro_files()
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    kokoro = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
    samples, sample_rate = kokoro.create(text, voice=voice)
    sf.write(str(destination), samples, sample_rate)
    return str(destination)
