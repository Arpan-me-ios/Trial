import subprocess
import sys
import time
import os
import argparse
from datetime import datetime
from pathlib import Path

from scripts.env_loader import load_local_env


PROJECT_ROOT = Path(__file__).resolve().parent
RUN_INTERVAL_SECONDS = 6 * 60 * 60
POLL_SECONDS = 60


def _run_pipeline(upload: bool) -> None:
    command = [sys.executable, str(PROJECT_ROOT / "pipeline.py"), "--type", "short", "--auto"]
    if upload:
        command.append("--upload")
    subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)


def main() -> None:
    load_local_env()
    parser = argparse.ArgumentParser(description="Run the YouTube pipeline every six hours.")
    parser.add_argument("--upload", action="store_true", help="Upload each rendered video to YouTube.")
    args = parser.parse_args()

    upload = args.upload or os.getenv("YT_PIPELINE_AUTO_UPLOAD", "0") == "1"
    last_run_at = 0.0
    while True:
        now = time.time()
        current = datetime.now()
        due_by_interval = now - last_run_at >= RUN_INTERVAL_SECONDS
        aligned_hour = current.hour in {0, 6, 12, 18}
        aligned_minute = current.minute == 0

        if last_run_at == 0.0 or due_by_interval or (aligned_hour and aligned_minute and due_by_interval):
            _run_pipeline(upload=upload)
            last_run_at = time.time()

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
