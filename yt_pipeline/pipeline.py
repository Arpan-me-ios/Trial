import argparse
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from scripts.env_loader import load_local_env
from scripts.model_downloader import MODEL_PATH, VOICES_PATH


PROJECT_ROOT = Path(__file__).resolve().parent
AUDIO_DIR = PROJECT_ROOT / "assets" / "audio"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "outputs"
BACKGROUND_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}


def _safe_slug(value: str, fallback: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() else "-" for character in value)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return (cleaned[:70] or fallback).strip("-")


def _metadata_path(video_path: str) -> Path:
    return Path(video_path).with_suffix(".json")


def check_setup() -> dict[str, Any]:
    load_local_env()
    workflow_path = PROJECT_ROOT / ".github" / "workflows" / "auto_post.yml"
    short_backgrounds = [
        path.name
        for path in (PROJECT_ROOT / "assets" / "backgrounds" / "short").glob("*")
        if path.suffix.lower() in BACKGROUND_EXTENSIONS
    ]
    long_backgrounds = [
        path.name
        for path in (PROJECT_ROOT / "assets" / "backgrounds" / "long").glob("*")
        if path.suffix.lower() in BACKGROUND_EXTENSIONS
    ]
    return {
        "gemini_api_key_present": bool(os.getenv("GEMINI_API_KEY")),
        "kokoro_model_present": MODEL_PATH.exists(),
        "kokoro_voices_present": VOICES_PATH.exists(),
        "youtube_upload_dry_run": os.getenv("YOUTUBE_UPLOAD_DRY_RUN", "1") == "1",
        "youtube_refresh_token_present": bool(os.getenv("YOUTUBE_REFRESH_TOKEN")),
        "youtube_client_id_present": bool(os.getenv("YOUTUBE_CLIENT_ID")),
        "youtube_client_secret_present": bool(os.getenv("YOUTUBE_CLIENT_SECRET")),
        "youtube_client_secret_file_present": Path(
            os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", str(PROJECT_ROOT / "client_secrets.json"))
        ).exists(),
        "youtube_privacy_status": os.getenv("YOUTUBE_PRIVACY_STATUS", "public"),
        "scheduler_auto_upload_enabled": os.getenv("YT_PIPELINE_AUTO_UPLOAD", "0") == "1",
        "github_workflow_present": workflow_path.exists(),
        "short_background_count": len(short_backgrounds),
        "long_background_count": len(long_backgrounds),
        "short_backgrounds": short_backgrounds[:10],
        "long_backgrounds": long_backgrounds[:10],
        "audio_dir": str(AUDIO_DIR),
        "output_dir": str(OUTPUT_DIR),
    }


def run_pipeline(content_type: str, auto_mode: bool, upload: bool = False) -> dict[str, Any]:
    if content_type not in {"short", "long"}:
        raise ValueError("content_type must be either 'short' or 'long'.")

    load_local_env()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    from scripts import caption_burner, script_generator, topic_picker, tts_engine, video_assembler

    topic = topic_picker.get_topic()
    script = script_generator.generate_script(topic=topic, video_type=content_type)
    run_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    title_slug = _safe_slug(script["title"], f"{content_type}-{run_id}")

    audio_path = AUDIO_DIR / f"{content_type}_{run_id}.wav"
    final_path = OUTPUT_DIR / f"{content_type}_{title_slug}_{run_id}.mp4"

    voiceover = tts_engine.generate_voiceover(script["body"], str(audio_path))
    base_video = video_assembler.assemble_video_base(voiceover, content_type)
    final_video = caption_burner.burn_captions(base_video, script["body"], str(final_path))
    upload_result = None
    if upload:
        from scripts import uploader

        upload_result = uploader.upload_to_youtube(final_video, script)

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
    parser.add_argument("--check", action="store_true", help="Print setup diagnostics without rendering.")
    args = parser.parse_args()

    if args.check:
        print(json.dumps(check_setup(), indent=2, ensure_ascii=False))
        return

    result = run_pipeline(content_type=args.type, auto_mode=args.auto, upload=args.upload)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
