from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timezone
from pathlib import Path
from typing import Iterable

from .evidence import RawEvidenceStore
from .telegram import TelegramEnvelope


@dataclass(frozen=True)
class TelegramCollectorConfig:
    api_id: int
    api_hash: str
    session: str
    channels: tuple[str, ...]
    media_root: Path


class TelegramCollector:
    """Telethon adapter with realtime + backfill semantics.

    Telethon remains an optional dependency. Import is delayed so benchmark-only installations do not
    need Telegram packages or credentials.
    """

    def __init__(self, config: TelegramCollectorConfig, evidence_store: RawEvidenceStore) -> None:
        self.config = config
        self.evidence_store = evidence_store
        self.config.media_root.mkdir(parents=True, exist_ok=True)

    async def run(self) -> None:
        try:
            from telethon import TelegramClient, events
        except ImportError as exc:  # pragma: no cover - exercised only with telegram extra installed
            raise RuntimeError("Install project with .[telegram] to run the collector") from exc

        client = TelegramClient(self.config.session, self.config.api_id, self.config.api_hash)
        await client.start()

        @client.on(events.Album(chats=list(self.config.channels)))
        async def on_album(event):
            await self._persist_messages(event.messages, edited=False)

        @client.on(events.NewMessage(chats=list(self.config.channels)))
        async def on_new(event):
            # Album items are handled as one logical envelope by the Album event.
            if getattr(event.message, "grouped_id", None) is not None:
                return
            await self._persist_messages([event.message], edited=False)

        @client.on(events.MessageEdited(chats=list(self.config.channels)))
        async def on_edit(event):
            await self._persist_messages([event.message], edited=True)

        await client.run_until_disconnected()

    async def backfill(self, limit_per_channel: int = 500) -> None:
        try:
            from telethon import TelegramClient
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install project with .[telegram] to run the collector") from exc

        async with TelegramClient(self.config.session, self.config.api_id, self.config.api_hash) as client:
            for channel in self.config.channels:
                async for message in client.iter_messages(channel, limit=limit_per_channel):
                    if getattr(message, "grouped_id", None) is not None:
                        # Backfill groups are still persisted idempotently per message; a later compactor can
                        # combine same grouped_id into one processing unit.
                        pass
                    await self._persist_messages([message], edited=False)

    async def _persist_messages(self, messages: Iterable, *, edited: bool) -> Path | None:
        messages = list(messages)
        if not messages:
            return None
        first = messages[0]
        channel_id = int(getattr(first, "chat_id", 0) or 0)
        media_paths: list[str] = []
        texts: list[str] = []
        for message in messages:
            text = getattr(message, "message", None)
            if text:
                texts.append(text)
            if getattr(message, "media", None) is not None:
                target = self.config.media_root / str(channel_id) / str(message.id)
                target.parent.mkdir(parents=True, exist_ok=True)
                downloaded = await message.download_media(file=str(target))
                if downloaded:
                    media_paths.append(str(downloaded))

        published = first.date
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        envelope = TelegramEnvelope(
            channel_id=channel_id,
            message_id=int(first.id),
            published_at=published,
            text="\n".join(texts) or None,
            grouped_id=getattr(first, "grouped_id", None),
            media_paths=tuple(media_paths),
            edited=edited,
        )
        return self.evidence_store.persist(envelope)


def run_collector(config: TelegramCollectorConfig, evidence_store: RawEvidenceStore) -> None:
    asyncio.run(TelegramCollector(config, evidence_store).run())
