import hashlib
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "kokoro-v1.0.onnx"
VOICES_PATH = PROJECT_ROOT / "models" / "voices-v1.0.bin"
DEFAULT_MODEL_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files-v1.0/kokoro-v1.0.onnx"
)
DEFAULT_VOICES_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files-v1.0/voices-v1.0.bin"
)


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(destination.suffix + ".download")
    request = Request(url, headers={"User-Agent": "yt-pipeline-kokoro-downloader/1.0"})

    try:
        with urlopen(request, timeout=120) as response:
            with temporary_path.open("wb") as output_file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output_file.write(chunk)
    except HTTPError as exc:
        raise RuntimeError(f"Failed to download {destination.name}: HTTP {exc.code} from {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Failed to download {destination.name}: {exc.reason} from {url}") from exc

    temporary_path.replace(destination)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _verify_checksum(path: Path, expected_hash: str | None) -> None:
    if not expected_hash:
        return
    actual_hash = _sha256(path)
    if actual_hash.lower() != expected_hash.lower():
        raise RuntimeError(
            f"Checksum mismatch for {path.name}. Expected {expected_hash}, got {actual_hash}."
        )


def ensure_kokoro_models() -> None:
    model_url = os.getenv("KOKORO_MODEL_URL", DEFAULT_MODEL_URL)
    voices_url = os.getenv("KOKORO_VOICES_URL", DEFAULT_VOICES_URL)
    model_sha256 = os.getenv("KOKORO_MODEL_SHA256")
    voices_sha256 = os.getenv("KOKORO_VOICES_SHA256")

    if not MODEL_PATH.exists():
        if not model_url:
            raise RuntimeError(
                "models/kokoro-v1.0.onnx is missing and KOKORO_MODEL_URL is not set."
            )
        _download_file(model_url, MODEL_PATH)
    if not VOICES_PATH.exists():
        if not voices_url:
            raise RuntimeError(
                "models/voices-v1.0.bin is missing and KOKORO_VOICES_URL is not set."
            )
        _download_file(voices_url, VOICES_PATH)

    _verify_checksum(MODEL_PATH, model_sha256)
    _verify_checksum(VOICES_PATH, voices_sha256)


if __name__ == "__main__":
    ensure_kokoro_models()
    print(f"Ready: {MODEL_PATH}")
    print(f"Ready: {VOICES_PATH}")
