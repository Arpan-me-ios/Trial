import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
RUN_INTERVAL_SECONDS = 6 * 60 * 60
POLL_SECONDS = 60


def _run_pipeline() -> None:
    command = [sys.executable, str(PROJECT_ROOT / "pipeline.py"), "--type", "short", "--auto"]
    subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)


def main() -> None:
    last_run_at = 0.0
    while True:
        now = time.time()
        current = datetime.now()
        due_by_interval = now - last_run_at >= RUN_INTERVAL_SECONDS
        aligned_hour = current.hour in {0, 6, 12, 18}
        aligned_minute = current.minute == 0

        if last_run_at == 0.0 or due_by_interval or (aligned_hour and aligned_minute and due_by_interval):
            _run_pipeline()
            last_run_at = time.time()

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
