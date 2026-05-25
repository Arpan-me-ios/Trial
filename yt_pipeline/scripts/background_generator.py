import random
from pathlib import Path

import numpy as np

try:
    from moviepy import VideoClip
except ImportError:
    from moviepy.editor import VideoClip


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _rect(image: np.ndarray, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int]) -> None:
    height, width = image.shape[:2]
    left = max(0, min(width, x1))
    right = max(0, min(width, x2))
    top = max(0, min(height, y1))
    bottom = max(0, min(height, y2))
    if right > left and bottom > top:
        image[top:bottom, left:right] = color


def _circle(image: np.ndarray, center_x: int, center_y: int, radius: int, color: tuple[int, int, int]) -> None:
    height, width = image.shape[:2]
    x1 = max(0, center_x - radius)
    x2 = min(width, center_x + radius + 1)
    y1 = max(0, center_y - radius)
    y2 = min(height, center_y + radius + 1)
    if x2 <= x1 or y2 <= y1:
        return
    yy, xx = np.ogrid[y1:y2, x1:x2]
    mask = (xx - center_x) ** 2 + (yy - center_y) ** 2 <= radius ** 2
    image[y1:y2, x1:x2][mask] = color


def _make_frame_factory(width: int, height: int, seed: int):
    rng = random.Random(seed)
    horizon = int(height * 0.30)
    road_top_width = int(width * 0.18)
    road_bottom_width = int(width * 0.96)
    center_x = width // 2

    y_axis = np.arange(height, dtype=np.float32)
    sky_mix = np.clip(y_axis / max(1, horizon), 0.0, 1.0)
    sky = (
        np.array([31, 51, 92], dtype=np.float32) * (1.0 - sky_mix[:, None])
        + np.array([92, 146, 210], dtype=np.float32) * sky_mix[:, None]
    )
    base = np.zeros((height, width, 3), dtype=np.uint8)
    base[:, :] = sky[:, None, :]
    base[horizon:, :] = np.array([32, 126, 76], dtype=np.uint8)

    obstacle_specs = []
    for index in range(28):
        obstacle_specs.append(
            {
                "lane": rng.choice([-1, 0, 1]),
                "offset": rng.uniform(0.0, 1.0),
                "kind": rng.choice(["crate", "barrier", "coin"]),
                "phase": index * 0.41 + rng.random(),
            }
        )

    def frame(t: float):
        image = base.copy()

        sun_x = int(width * 0.78)
        sun_y = int(height * 0.12)
        _circle(image, sun_x, sun_y, int(width * 0.045), (255, 211, 91))

        for layer in range(3):
            scroll = int((t * (22 + layer * 18)) % max(1, width))
            y = int(horizon * (0.52 + layer * 0.13))
            block_w = int(width * (0.09 + layer * 0.025))
            block_h = int(height * (0.035 + layer * 0.014))
            for x in range(-block_w, width + block_w, block_w * 2):
                _rect(
                    image,
                    x + scroll,
                    y - block_h,
                    x + scroll + block_w,
                    y,
                    (22 + layer * 18, 45 + layer * 15, 76 + layer * 13),
                )

        for y in range(horizon, height):
            depth = (y - horizon) / max(1, height - horizon)
            half_width = int((road_top_width + (road_bottom_width - road_top_width) * depth) / 2)
            shade = int(46 + depth * 54)
            image[y, center_x - half_width : center_x + half_width] = (shade, shade, shade + 8)

        lane_color = (232, 232, 218)
        for lane in (-1, 1):
            for y in range(horizon, height, 5):
                depth = (y - horizon) / max(1, height - horizon)
                half_width = int((road_top_width + (road_bottom_width - road_top_width) * depth) / 2)
                lane_x = int(center_x + lane * half_width * 0.34)
                stripe_width = max(2, int(2 + depth * width * 0.010))
                if int((y + t * 520) / max(12, int(70 * depth + 12))) % 2 == 0:
                    _rect(image, lane_x - stripe_width, y, lane_x + stripe_width, y + 5, lane_color)

        for spec in obstacle_specs:
            progress = (spec["offset"] + t * 0.26 + spec["phase"] * 0.03) % 1.0
            eased = progress * progress
            y = int(horizon + eased * (height - horizon + height * 0.20))
            if y < horizon or y > height + 80:
                continue
            depth = (y - horizon) / max(1, height - horizon)
            road_half = int((road_top_width + (road_bottom_width - road_top_width) * depth) / 2)
            lane_spacing = road_half * 0.46
            x = int(center_x + spec["lane"] * lane_spacing)
            size = max(8, int(width * (0.018 + depth * 0.075)))

            if spec["kind"] == "coin":
                _circle(image, x, y, size // 2, (255, 205, 52))
                _circle(image, x, y, max(2, size // 4), (255, 245, 139))
            elif spec["kind"] == "barrier":
                _rect(image, x - size, y - size // 2, x + size, y + size // 2, (220, 65, 54))
                _rect(image, x - size, y - size // 8, x + size, y + size // 8, (255, 235, 118))
            else:
                _rect(image, x - size, y - size, x + size, y + size, (125, 78, 42))
                _rect(image, x - size, y - size, x + size, y - size + max(2, size // 5), (188, 130, 73))

        player_y = int(height * 0.78)
        player_x = int(center_x + np.sin(t * 1.7) * width * 0.09)
        player_w = int(width * 0.070)
        player_h = int(height * 0.070)
        _rect(image, player_x - player_w, player_y - player_h, player_x + player_w, player_y + player_h, (53, 114, 236))
        _rect(image, player_x - player_w // 2, player_y - player_h - player_w, player_x + player_w // 2, player_y - player_h, (255, 204, 144))
        _rect(image, player_x - player_w, player_y + player_h, player_x - player_w // 4, player_y + player_h * 2, (34, 62, 120))
        _rect(image, player_x + player_w // 4, player_y + player_h, player_x + player_w, player_y + player_h * 2, (34, 62, 120))

        score_width = int(width * 0.42)
        _rect(image, int(width * 0.06), int(height * 0.035), int(width * 0.06) + score_width, int(height * 0.067), (18, 24, 38))
        _rect(image, int(width * 0.065), int(height * 0.041), int(width * 0.065) + int(score_width * ((t * 0.07) % 1.0)), int(height * 0.061), (72, 214, 119))

        return image

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
