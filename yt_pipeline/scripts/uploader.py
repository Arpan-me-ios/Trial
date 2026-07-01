import json
import os
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

from scripts.env_loader import load_local_env


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_OAUTH_SECRETS_PATH = PROJECT_ROOT / "youtube_oauth_secrets.json"


def _local_oauth_value(key: str) -> str:
    if os.getenv(key):
        return os.getenv(key, "")
    if not LOCAL_OAUTH_SECRETS_PATH.exists():
        return ""
    try:
        payload = json.loads(LOCAL_OAUTH_SECRETS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    value = payload.get(key, "")
    return str(value) if value else ""


def _load_credentials():
    load_local_env()
    refresh_token = _local_oauth_value("YOUTUBE_REFRESH_TOKEN")
    client_id = _local_oauth_value("YOUTUBE_CLIENT_ID")
    client_secret = _local_oauth_value("YOUTUBE_CLIENT_SECRET")
    token_uri = _local_oauth_value("YOUTUBE_TOKEN_URI") or "https://oauth2.googleapis.com/token"
    if refresh_token and client_id and client_secret:
        return Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )

    client_secret_file = os.getenv(
        "YOUTUBE_CLIENT_SECRETS_FILE",
        str(PROJECT_ROOT / "client_secrets.json"),
    )
    if not Path(client_secret_file).exists():
        raise FileNotFoundError(
            "YouTube OAuth client secret file was not found. Set YOUTUBE_CLIENT_SECRETS_FILE "
            f"or place client_secrets.json at {PROJECT_ROOT}. This upload helper prepares the "
            "official YouTube Data API v3 request and requires your own OAuth client."
        )

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    return flow.run_local_server(port=0)


def upload_to_youtube(video_path: str, metadata: dict[str, Any]):
    load_local_env()
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file does not exist: {path}")

    title = str(metadata.get("title", "Automated Story")).strip()[:100]
    description = str(metadata.get("description", "")).strip()
    raw_tags = metadata.get("tags", [])
    if isinstance(raw_tags, str):
        tags = [tag.strip().lstrip("#") for tag in raw_tags.split(",") if tag.strip()]
    else:
        tags = [str(tag).strip().lstrip("#") for tag in raw_tags if str(tag).strip()]
    privacy_status = os.getenv("YOUTUBE_PRIVACY_STATUS", "public").strip().lower()
    if privacy_status not in {"public", "private", "unlisted"}:
        raise ValueError(
            "YOUTUBE_PRIVACY_STATUS must be one of: public, private, unlisted."
        )

    if os.getenv("YOUTUBE_UPLOAD_DRY_RUN", "1") == "1":
        return {
            "dry_run": True,
            "video_path": str(path),
            "request_body": {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False,
                },
            },
        }

    credentials = _load_credentials()
    youtube = build("youtube", "v3", credentials=credentials)
    media = MediaFileUpload(str(path), chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        },
        media_body=media,
    )
    return request.execute()
