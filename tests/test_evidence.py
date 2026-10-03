from datetime import datetime, timezone
from pathlib import Path

from hhpi.ingest.evidence import RawEvidenceStore
from hhpi.ingest.telegram import TelegramEnvelope


def test_evidence_store_is_idempotent_and_versions_edits(tmp_path: Path):
    media = tmp_path / "photo.jpg"
    media.write_bytes(b"fake-image")
    store = RawEvidenceStore(tmp_path / "raw")
    env = TelegramEnvelope(
        channel_id=123,
        message_id=9,
        published_at=datetime(2026, 9, 29, tzinfo=timezone.utc),
        text="list",
        grouped_id=None,
        media_paths=(str(media),),
    )
    first = store.persist(env)
    second = store.persist(env)
    assert first == second

    edited = TelegramEnvelope(**{**env.__dict__, "text": "edited", "edited": True})
    version = store.persist(edited)
    assert version != first
    assert ".versions" in str(version)
