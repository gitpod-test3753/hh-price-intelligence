from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Hashable


@dataclass(frozen=True)
class FieldCandidate:
    engine: str
    value: Hashable | None
    confidence: float


@dataclass(frozen=True)
class ConsensusResult:
    value: Hashable | None
    confidence: float
    agreement_ratio: float
    engines: tuple[str, ...]
    needs_escalation: bool


def consensus(
    candidates: list[FieldCandidate],
    *,
    min_agreement: float = 0.66,
    min_confidence: float = 0.80,
) -> ConsensusResult:
    valid = [c for c in candidates if c.value is not None]
    if not valid:
        return ConsensusResult(None, 0.0, 0.0, (), True)

    grouped: dict[Hashable, list[FieldCandidate]] = defaultdict(list)
    for candidate in valid:
        grouped[candidate.value].append(candidate)

    def group_score(item: tuple[Hashable, list[FieldCandidate]]) -> tuple[int, float]:
        _, group = item
        return len(group), sum(c.confidence for c in group) / len(group)

    value, winners = max(grouped.items(), key=group_score)
    avg_conf = sum(c.confidence for c in winners) / len(winners)
    agreement = len(winners) / len(valid)
    needs = agreement < min_agreement or avg_conf < min_confidence
    return ConsensusResult(
        value=value,
        confidence=round(avg_conf, 4),
        agreement_ratio=round(agreement, 4),
        engines=tuple(sorted(c.engine for c in winners)),
        needs_escalation=needs,
    )
