"""One-shot migrate + seed when a web worker boots (Render-friendly)."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def should_bootstrap() -> bool:
    flag = os.environ.get("BOOTSTRAP_ON_START", "").strip().lower()
    if flag in {"0", "false", "no"}:
        return False
    if flag in {"1", "true", "yes"}:
        return True
    return bool(os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"))


def run_bootstrap() -> None:
    if not should_bootstrap():
        return

    from django.core.management import call_command

    logger.info("Running migrate + seed_catalog on worker start")
    call_command("migrate", interactive=False, verbosity=1)
    call_command("seed_catalog", verbosity=1)
