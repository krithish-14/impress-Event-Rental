"""Render/production start: migrate, seed catalog, then run gunicorn."""
from __future__ import annotations

import os
import subprocess
import sys


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd)


def main() -> None:
    run([sys.executable, "manage.py", "migrate", "--noinput"])
    run([sys.executable, "manage.py", "collectstatic", "--noinput"])
    run([sys.executable, "manage.py", "seed_catalog"])
    port = os.environ.get("PORT", "8000")
    os.execvp(
        sys.executable,
        [
            sys.executable,
            "-m",
            "gunicorn",
            "config.wsgi:application",
            "--bind",
            f"0.0.0.0:{port}",
            "--workers",
            "2",
            "--timeout",
            "120",
        ],
    )


if __name__ == "__main__":
    main()
