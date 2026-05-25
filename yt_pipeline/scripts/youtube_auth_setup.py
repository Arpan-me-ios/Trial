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

    client_secret_path = Path(client_secret_file)
    client_secret_payload = json.loads(client_secret_path.read_text(encoding="utf-8"))
    client_config = (
        client_secret_payload.get("installed")
        or client_secret_payload.get("web")
        or {}
    )
    client_id = client_config.get("client_id", "")
    client_secret = client_config.get("client_secret", "")
    if not client_id or not client_secret:
        raise ValueError(
            "The OAuth JSON does not contain client_id and client_secret under an installed "
            "or web section. Create a Desktop app OAuth client and download its JSON again."
        )

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    credentials = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    result = {
        "YOUTUBE_CLIENT_ID": client_id,
        "YOUTUBE_CLIENT_SECRET": client_secret,
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
