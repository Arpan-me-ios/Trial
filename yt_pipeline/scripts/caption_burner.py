import os
import re
from pathlib import Path

try:
    from moviepy import ColorClip, CompositeVideoClip, TextClip, VideoFileClip
except ImportError:
    from moviepy.editor import ColorClip, CompositeVideoClip, TextClip, VideoFileClip


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _clip_duration(clip: object) -> float:
    duration = getattr(clip, "duration", None)
    if duration is None:
        raise ValueError("MoviePy clip has no duration metadata.")
    return float(duration)


def _with_timing(clip: object, start: float, duration: float):
    if hasattr(clip, "with_start"):
        clip = clip.with_start(start)
    else:
        clip = clip.set_start(start)

    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)


def _with_position(clip: object, position):
    if hasattr(clip, "with_position"):
        return clip.with_position(position)
    return clip.set_position(position)


def _with_opacity(clip: object, opacity: float):
    if hasattr(clip, "with_opacity"):
        return clip.with_opacity(opacity)
    return clip.set_opacity(opacity)


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


def _caption_units(text_script: str) -> list[str]:
    words = re.findall(r"\S+", text_script)
    units = []
    for index in range(0, len(words), 4):
        unit = " ".join(words[index : index + 4])
        if unit:
            units.append(unit)
    return units


def _make_text_clip(text: str, video_width: int):
    clip_width = max(320, int(video_width * 0.90))
    font_size = max(42, min(88, int(video_width * 0.068)))
    common = {
        "color": "white",
        "stroke_color": "black",
        "stroke_width": max(4, int(font_size * 0.095)),
        "method": "caption",
        "size": (clip_width, None),
    }
    attempts = (
        {
            "text": text,
            "font_size": font_size,
            "font": "DejaVu-Sans-Bold",
            "margin": (24, 10),
            "text_align": "center",
            **common,
        },
        {
            "txt": text,
            "fontsize": font_size,
            "font": "DejaVu-Sans-Bold",
            "align": "center",
            **common,
        },
        {
            "text": text,
            "font_size": font_size,
            "margin": (24, 10),
            "text_align": "center",
            **common,
        },
        {
            "txt": text,
            "fontsize": font_size,
            "color": "white",
            "stroke_color": "black",
            "stroke_width": max(4, int(font_size * 0.095)),
            "method": "caption",
            "size": (clip_width, None),
            "align": "center",
        },
    )
    last_error = None
    for kwargs in attempts:
        try:
            return TextClip(**kwargs)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Unable to create caption TextClip: {last_error}") from last_error


def _caption_position(text_clip: object, video_width: int, video_height: int) -> tuple[int, int]:
    text_width = int(getattr(text_clip, "w", video_width * 0.88))
    text_height = int(getattr(text_clip, "h", video_height * 0.06))
    vertical_ratio = float(os.getenv("CAPTION_VERTICAL_RATIO", "0.48"))
    x = max(0, (video_width - text_width) // 2)
    y = max(0, min(video_height - text_height, int(video_height * vertical_ratio)))
    return x, y


def _make_red_accent(text_clip: object, video_width: int):
    text_width = int(getattr(text_clip, "w", video_width * 0.80))
    text_height = int(getattr(text_clip, "h", 72))
    bar_width = max(120, min(int(text_width * 0.72), int(video_width * 0.74)))
    bar_height = max(10, min(24, int(text_height * 0.22)))
    return ColorClip(size=(bar_width, bar_height), color=(238, 45, 38))


def burn_captions(video_path: str, text_script: str, output_path: str) -> str:
    source = Path(video_path)
    if not source.exists():
        raise FileNotFoundError(f"Video file does not exist: {source}")
    if not text_script.strip():
        raise ValueError("text_script is empty; cannot create captions.")

    destination = Path(output_path)
    if not destination.is_absolute():
        destination = PROJECT_ROOT / "assets" / "outputs" / destination
    destination.parent.mkdir(parents=True, exist_ok=True)

    video = VideoFileClip(str(source))
    final = None
    caption_clips = []
    try:
        duration = _clip_duration(video)
        units = _caption_units(text_script)
        unit_duration = max(0.75, duration / max(1, len(units)))

        for index, unit in enumerate(units):
            start = min(duration, index * unit_duration)
            remaining = max(0.1, duration - start)
            active_duration = min(unit_duration, remaining)
            text_clip = _make_text_clip(unit, int(video.w))
            text_x, text_y = _caption_position(text_clip, int(video.w), int(video.h))
            accent_clip = _make_red_accent(text_clip, int(video.w))
            accent_x = int((int(video.w) - int(getattr(accent_clip, "w", video.w * 0.6))) / 2)
            accent_y = text_y + int(getattr(text_clip, "h", 72) * 0.66)
            accent_clip = _with_opacity(accent_clip, 0.95)
            accent_clip = _with_position(accent_clip, (accent_x, accent_y))
            accent_clip = _with_timing(accent_clip, start, active_duration)
            caption_clips.append(accent_clip)

            text_clip = _with_position(text_clip, (text_x, text_y))
            text_clip = _with_timing(text_clip, start, active_duration)
            caption_clips.append(text_clip)

        final = CompositeVideoClip([video, *caption_clips])
        _write_video(final, destination)
    finally:
        if final is not None:
            final.close()
        for caption_clip in caption_clips:
            caption_clip.close()
        video.close()

    return str(destination)
