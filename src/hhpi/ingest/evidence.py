from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from .telegram import TelegramEnvelope


class RawEvidenceStore:
    """Immutable filesystem evidence store for development and local replay.

    Production can swap this for S3/MinIO without changing collector semantics.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def persist(self, envelope: TelegramEnvelope) -> Path:
        channel_dir = self.root / str(envelope.channel_id)
        channel_dir.mkdir(parents=True, exist_ok=True)
        target = channel_dir / f"{envelope.message_id}.json"

        payload = asdict(envelope)
        payload["published_at"] = envelope.published_at.isoformat()
        payload["media"] = [self._describe_media(Path(p)) for p in envelope.media_paths]
        payload["envelope_sha256"] = sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if target.exists():
            existing = json.loads(target.read_text(encoding="utf-8"))
            # Identical replays are idempotent. Changed messages must be versioned explicitly.
            if existing.get("envelope_sha256") == payload["envelope_sha256"]:
                return target
            version_dir = channel_dir / f"{envelope.message_id}.versions"
            version_dir.mkdir(exist_ok=True)
            version_target = version_dir / f"{payload['envelope_sha256']}.json"
            if not version_target.exists():
                version_target.write_text(encoded, encoding="utf-8")
            return version_target

        target.write_text(encoded, encoding="utf-8")
        return target

    @staticmethod
    def _describe_media(path: Path) -> dict:
        if not path.exists():
            return {"path": str(path), "exists": False}
        data = path.read_bytes()
        return {
            "path": str(path),
            "exists": True,
            "bytes": len(data),
            "sha256": sha256(data).hexdigest(),
        }
