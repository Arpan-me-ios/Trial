import json
import os
import random
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
SAFE_GAMEPLAY_QUERIES = [
    "mobile game",
    "arcade game",
    "video game",
    "gaming",
    "racing game",
    "runner game",
    "game controller",
    "esports",
]


def _request_json(url: str, api_key: str) -> dict:
    request = Request(url, headers={"Authorization": api_key, "User-Agent": "yt-pipeline/1.0"})
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"Pexels API request failed with HTTP {exc.code}: {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Pexels API request failed: {exc.reason}") from exc


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(destination.suffix + ".download")
    request = Request(url, headers={"User-Agent": "yt-pipeline/1.0"})
    try:
        with urlopen(request, timeout=180) as response:
            with temporary_path.open("wb") as output_file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output_file.write(chunk)
    except HTTPError as exc:
        raise RuntimeError(f"Stock video download failed with HTTP {exc.code}: {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Stock video download failed: {exc.reason}") from exc
    temporary_path.replace(destination)


def _best_video_file(video: dict, prefer_portrait: bool) -> dict | None:
    files = [
        file
        for file in video.get("video_files", [])
        if str(file.get("file_type", "")).lower() == "video/mp4" and file.get("link")
    ]
    if not files:
        return None

    def score(file: dict) -> tuple[int, int, int]:
        width = int(file.get("width") or 0)
        height = int(file.get("height") or 0)
        orientation_score = 1 if height >= width else 0
        if not prefer_portrait:
            orientation_score = 1 if width >= height else 0
        target_edge = 1280
        size_penalty = abs((height if prefer_portrait else width) - target_edge)
        return (orientation_score, -size_penalty, width * height)

    return max(files, key=score)


def download_pexels_gameplay_backgrounds(video_type: str = "short", minimum_count: int = 5) -> list[Path]:
    if video_type not in {"short", "long"}:
        raise ValueError("video_type must be either 'short' or 'long'.")

    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("PEXELS_API_KEY is not set; skipping stock gameplay download.", flush=True)
        return []

    directory = PROJECT_ROOT / "assets" / "backgrounds" / video_type
    directory.mkdir(parents=True, exist_ok=True)
    existing = sorted(directory.glob("stock_pexels_*.mp4"))
    if len(existing) >= minimum_count:
        print(f"Using {len(existing)} cached stock gameplay videos.", flush=True)
        return existing

    needed = minimum_count - len(existing)
    downloaded: list[Path] = []
    seen_ids = {path.stem.replace("stock_pexels_", "") for path in existing}
    queries = SAFE_GAMEPLAY_QUERIES[:]
    random.shuffle(queries)

    for query in queries:
        if len(downloaded) >= needed:
            break
        params = {
            "query": query,
            "orientation": "portrait" if video_type == "short" else "landscape",
            "per_page": 8,
            "page": random.randint(1, 3),
        }
        payload = _request_json(f"{PEXELS_SEARCH_URL}?{urlencode(params)}", api_key)
        videos = payload.get("videos", [])
        random.shuffle(videos)

        for video in videos:
            if len(downloaded) >= needed:
                break
            video_id = str(video.get("id", "")).strip()
            if not video_id or video_id in seen_ids:
                continue
            chosen_file = _best_video_file(video, prefer_portrait=video_type == "short")
            if not chosen_file:
                continue

            output_path = directory / f"stock_pexels_{video_id}.mp4"
            credit_path = directory / f"stock_pexels_{video_id}.json"
            _download_file(chosen_file["link"], output_path)
            credit_path.write_text(
                json.dumps(
                    {
                        "source": "Pexels",
                        "pexels_video_id": video_id,
                        "url": video.get("url"),
                        "author": (video.get("user") or {}).get("name"),
                        "query": query,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            seen_ids.add(video_id)
            downloaded.append(output_path)
            print(f"Downloaded stock gameplay background: {output_path.name}", flush=True)

    return sorted(directory.glob("stock_pexels_*.mp4"))


if __name__ == "__main__":
    clips = download_pexels_gameplay_backgrounds(video_type=os.getenv("VIDEO_TYPE", "short"))
    print(f"Ready stock clips: {len(clips)}")
