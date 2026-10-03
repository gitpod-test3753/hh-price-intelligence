"""Telegram ingestion contract.

Implementation intentionally isolates Telegram-specific concerns from extraction logic.
The production adapter will persist raw messages/media before any OCR is attempted.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TelegramEnvelope:
    channel_id: int
    message_id: int
    published_at: datetime
    text: str | None
    grouped_id: int | None
    media_paths: tuple[str, ...]
    edited: bool = False
