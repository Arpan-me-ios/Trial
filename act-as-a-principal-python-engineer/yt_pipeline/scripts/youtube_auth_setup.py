import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main() -> None:
    client_secret_file = os.getenv(
        "YOUTUBE_CLIENT_SECRETS_FILE",
        str(PROJECT_ROOT / "client_secrets.json"),
    )
    if not Path(client_secret_file).exists():
        raise FileNotFoundError(
            "Download your OAuth Desktop client JSON from Google Cloud and save it as "
            f"{PROJECT_ROOT / 'client_secrets.json'}, or set YOUTUBE_CLIENT_SECRETS_FILE."
        )

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    credentials = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    client_config = flow.client_config.get("installed") or flow.client_config.get("web") or {}
    result = {
        "YOUTUBE_CLIENT_ID": client_config.get("client_id", ""),
        "YOUTUBE_CLIENT_SECRET": client_config.get("client_secret", ""),
        "YOUTUBE_REFRESH_TOKEN": credentials.refresh_token or "",
        "YOUTUBE_UPLOAD_DRY_RUN": "0",
    }

    print("\nAdd these as GitHub repository secrets:\n")
    for key, value in result.items():
        print(f"{key}={value}")

    output_path = PROJECT_ROOT / "youtube_oauth_secrets.json"
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nA local copy was written to {output_path}. Do not commit this file.")


if __name__ == "__main__":
    main()
