import math
import random
from pathlib import Path

import numpy as np

try:
    from moviepy import VideoClip
except ImportError:
    from moviepy.editor import VideoClip


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _make_frame_factory(width: int, height: int, seed: int):
    rng = random.Random(seed)
    base_a = np.array([rng.randint(12, 55), rng.randint(12, 55), rng.randint(18, 70)], dtype=np.float32)
    base_b = np.array([rng.randint(70, 160), rng.randint(45, 135), rng.randint(40, 145)], dtype=np.float32)
    accent = np.array([rng.randint(120, 245), rng.randint(105, 225), rng.randint(90, 220)], dtype=np.float32)

    x_axis = np.linspace(0.0, 1.0, width, dtype=np.float32)
    y_axis = np.linspace(0.0, 1.0, height, dtype=np.float32)
    xx, yy = np.meshgrid(x_axis, y_axis)
    vignette = np.sqrt((xx - 0.5) ** 2 + (yy - 0.5) ** 2)
    vignette = np.clip(1.0 - vignette * 1.25, 0.25, 1.0)

    def frame(t: float):
        wave = 0.5 + 0.5 * np.sin((xx * 4.5) + (yy * 3.0) + (t * 0.7))
        drift = 0.5 + 0.5 * np.cos((xx * 2.2) - (yy * 5.0) + (t * 0.45))
        pulse = 0.5 + 0.5 * math.sin(t * 0.9)

        image = base_a * (1.0 - wave[..., None]) + base_b * wave[..., None]
        image = image * (0.82 + 0.18 * drift[..., None])

        glow_x = 0.5 + 0.22 * math.sin(t * 0.31 + seed)
        glow_y = 0.45 + 0.20 * math.cos(t * 0.27 + seed)
        glow = np.exp(-(((xx - glow_x) ** 2) / 0.055 + ((yy - glow_y) ** 2) / 0.09))
        image = image + accent * glow[..., None] * (0.26 + 0.16 * pulse)

        scanline = 1.0 - (0.035 * (np.sin((yy * height * 0.09) + (t * 3.0)) > 0))
        image = image * scanline[..., None] * vignette[..., None]
        return np.clip(image, 0, 255).astype(np.uint8)

    return frame


def ensure_generated_backgrounds(video_type: str, minimum_count: int = 3) -> list[Path]:
    if video_type not in {"short", "long"}:
        raise ValueError("video_type must be either 'short' or 'long'.")

    directory = PROJECT_ROOT / "assets" / "backgrounds" / video_type
    directory.mkdir(parents=True, exist_ok=True)

    width, height = (1080, 1920) if video_type == "short" else (1920, 1080)
    duration = 12 if video_type == "short" else 24
    fps = 30

    created = []
    existing = sorted(directory.glob("generated_*.mp4"))
    missing_count = max(0, minimum_count - len(existing))

    for index in range(missing_count):
        seed = random.randint(100_000, 999_999)
        output_path = directory / f"generated_{video_type}_{seed}.mp4"
        try:
            clip = VideoClip(frame_function=_make_frame_factory(width, height, seed), duration=duration)
        except TypeError:
            clip = VideoClip(make_frame=_make_frame_factory(width, height, seed), duration=duration)

        try:
            clip.write_videofile(
                str(output_path),
                codec="libx264",
                audio=False,
                fps=fps,
                preset="medium",
                threads=4,
                logger=None,
            )
        finally:
            clip.close()
        created.append(output_path)

    return sorted(directory.glob("generated_*.mp4")) + created
