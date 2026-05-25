import random
import uuid
from pathlib import Path

try:
    from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips
except ImportError:
    from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips

from scripts.background_generator import ensure_generated_backgrounds


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKGROUND_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}


def _clip_duration(clip: object) -> float:
    duration = getattr(clip, "duration", None)
    if duration is None:
        raise ValueError("MoviePy clip has no duration metadata.")
    return float(duration)


def _subclip(clip: object, start: float, end: float):
    if hasattr(clip, "subclipped"):
        return clip.subclipped(start, end)
    return clip.subclip(start, end)


def _with_audio(video_clip: object, audio_clip: object):
    if hasattr(video_clip, "with_audio"):
        return video_clip.with_audio(audio_clip)
    return video_clip.set_audio(audio_clip)


def _write_video(clip: object, output_path: Path) -> None:
    clip.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="medium",
        threads=4,
        logger=None,
    )


def _available_backgrounds(directory: Path) -> list[Path]:
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    files = [
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in BACKGROUND_EXTENSIONS
    ]
    return files


def _loop_to_duration(background_path: Path, target_duration: float):
    base_clip = VideoFileClip(str(background_path))
    base_duration = _clip_duration(base_clip)
    if base_duration <= 0:
        base_clip.close()
        raise ValueError(f"Background clip has invalid duration: {background_path}")

    clips: list[object] = []
    remaining = target_duration
    while remaining > 0:
        segment_duration = min(base_duration, remaining)
        clips.append(_subclip(base_clip, 0, segment_duration))
        remaining -= segment_duration

    if len(clips) == 1:
        return clips[0]
    return concatenate_videoclips(clips, method="compose")


def assemble_video_base(audio_path: str, video_type: str) -> str:
    if video_type not in {"short", "long"}:
        raise ValueError("video_type must be either 'short' or 'long'.")

    audio_file = Path(audio_path)
    if not audio_file.exists():
        raise FileNotFoundError(f"Voiceover file does not exist: {audio_file}")

    background_dir = PROJECT_ROOT / "assets" / "backgrounds" / video_type
    backgrounds = _available_backgrounds(background_dir)
    if not backgrounds:
        ensure_generated_backgrounds(video_type=video_type, minimum_count=1)
        backgrounds = _available_backgrounds(background_dir)
    if not backgrounds:
        raise FileNotFoundError(f"Could not create or find background videos in {background_dir}.")
    background_path = random.choice(backgrounds)

    output_dir = PROJECT_ROOT / "assets" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"base_{video_type}_{uuid.uuid4().hex}.mp4"

    audio_clip = AudioFileClip(str(audio_file))
    video_clip = None
    final_clip = None
    try:
        audio_duration = _clip_duration(audio_clip)
        if audio_duration <= 0:
            raise ValueError(f"Voiceover duration must be positive: {audio_file}")
        video_clip = _loop_to_duration(background_path, audio_duration)
        trimmed_video = _subclip(video_clip, 0, audio_duration)
        final_clip = _with_audio(trimmed_video, audio_clip)
        _write_video(final_clip, output_path)
    finally:
        if final_clip is not None:
            final_clip.close()
        if video_clip is not None:
            video_clip.close()
        audio_clip.close()

    return str(output_path)
