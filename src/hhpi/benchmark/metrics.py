from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

FIELDS = ("model", "ram", "storage", "network", "color", "price")


@dataclass
class FieldScore:
    correct: int = 0
    total: int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0


def exact_match_metrics(gold_rows: list[dict], pred_rows: list[dict], key: str = "row_id") -> dict:
    pred = {r[key]: r for r in pred_rows}
    scores: dict[str, FieldScore] = defaultdict(FieldScore)
    complete_correct = 0

    for gold in gold_rows:
        candidate = pred.get(gold[key], {})
        row_ok = True
        for field in FIELDS:
            if field not in gold:
                continue
            scores[field].total += 1
            ok = candidate.get(field) == gold.get(field)
            scores[field].correct += int(ok)
            row_ok &= ok
        complete_correct += int(row_ok)

    return {
        "fields": {name: round(score.accuracy, 6) for name, score in scores.items()},
        "row_exact_accuracy": round(complete_correct / len(gold_rows), 6) if gold_rows else 0.0,
        "row_recall": round(sum(1 for r in gold_rows if r[key] in pred) / len(gold_rows), 6)
        if gold_rows
        else 0.0,
    }
