from hhpi.benchmark.metrics import exact_match_metrics


def test_exact_metrics_penalize_price_error():
    gold = [{"row_id": "1", "model": "note15", "ram": 8, "storage": 256, "color": "black", "price": 81000000}]
    pred = [{"row_id": "1", "model": "note15", "ram": 8, "storage": 256, "color": "black", "price": 61000000}]
    m = exact_match_metrics(gold, pred)
    assert m["fields"]["price"] == 0
    assert m["fields"]["model"] == 1
    assert m["row_exact_accuracy"] == 0
