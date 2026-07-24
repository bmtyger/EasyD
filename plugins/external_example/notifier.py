"""External example: a custom notifier plugin."""

from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger(__name__)


def publish(event: str, payload: dict[str, Any]) -> None:
    log.info("external_example event=%s payload=%s", event, payload)
    # drop to desktop notifier, webhook, or anything else
