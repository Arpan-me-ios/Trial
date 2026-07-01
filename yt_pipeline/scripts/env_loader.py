import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_local_env() -> None:
    env_files = (
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / ".env.local",
    )
    for env_file in env_files:
        if not env_file.exists():
            continue
        for line_number, raw_line in enumerate(env_file.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not key:
                raise ValueError(f"Invalid empty environment key in {env_file} on line {line_number}.")
            os.environ.setdefault(key, value)
