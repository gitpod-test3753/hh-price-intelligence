from hhpi.extraction.ensemble import FieldCandidate, consensus


def test_consensus_accepts_agreeing_engines():
    result = consensus(
        [
            FieldCandidate("a", 88_500_000, 0.98),
            FieldCandidate("b", 88_500_000, 0.94),
            FieldCandidate("c", 86_500_000, 0.91),
        ]
    )
    assert result.value == 88_500_000
    assert result.agreement_ratio > 0.66
    assert result.needs_escalation is False


def test_consensus_escalates_disagreement():
    result = consensus(
        [
            FieldCandidate("a", 88_500_000, 0.99),
            FieldCandidate("b", 86_500_000, 0.99),
        ]
    )
    assert result.needs_escalation is True
