import argparse
import json
import time
import uuid
from pathlib import Path
from typing import Any

from scripts import caption_burner, script_generator, topic_picker, tts_engine, uploader, video_assembler


PROJECT_ROOT = Path(__file__).resolve().parent
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "outputs"


def _safe_slug(value: str, fallback: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() else "-" for character in value)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return (cleaned[:70] or fallback).strip("-")


def _metadata_path(video_path: str) -> Path:
    return Path(video_path).with_suffix(".json")


def run_pipeline(content_type: str, auto_mode: bool, upload: bool = False) -> dict[str, Any]:
    if content_type not in {"short", "long"}:
        raise ValueError("content_type must be either 'short' or 'long'.")

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    topic = topic_picker.get_topic()
    script = script_generator.generate_script(topic=topic, video_type=content_type)
    run_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    title_slug = _safe_slug(script["title"], f"{content_type}-{run_id}")

    audio_path = AUDIO_DIR / f"{content_type}_{run_id}.wav"
    final_path = OUTPUT_DIR / f"{content_type}_{title_slug}_{run_id}.mp4"

    voiceover = tts_engine.generate_voiceover(script["body"], str(audio_path))
    base_video = video_assembler.assemble_video_base(voiceover, content_type)
    final_video = caption_burner.burn_captions(base_video, script["body"], str(final_path))
    upload_result = uploader.upload_to_youtube(final_video, script) if upload else None

    result = {
        "auto_mode": auto_mode,
        "content_type": content_type,
        "topic": topic,
        "script": script,
        "voiceover_path": voiceover,
        "base_video_path": base_video,
        "final_video_path": final_video,
        "upload_result": upload_result,
    }

    metadata_file = _metadata_path(final_video)
    metadata_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    result["metadata_path"] = str(metadata_file)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate automated YouTube Shorts or long-form videos.")
    parser.add_argument("--type", choices=["short", "long"], default="short", help="Video format to render.")
    parser.add_argument("--auto", action="store_true", help="Run in unattended automation mode.")
    parser.add_argument("--upload", action="store_true", help="Upload the rendered video to YouTube.")
    args = parser.parse_args()

    result = run_pipeline(content_type=args.type, auto_mode=args.auto, upload=args.upload)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
