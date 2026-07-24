"""Lightweight in-process event bus."""

from __future__ import annotations

import logging
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event: str, handler: Callable) -> None:
        self._subscribers.setdefault(event, []).append(handler)

    def publish(self, event: str, payload: dict) -> None:
        logger.info("EVENT %s payload=%s", event, payload)
        for handler in self._subscribers.get(event, []):
            try:
                handler(payload)
            except Exception as exc:
                logger.exception("Event handler failed for %s", event)
