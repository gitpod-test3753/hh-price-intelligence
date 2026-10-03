from hhpi.validation.price import validate_price


def test_price_validation_flags_large_ocr_jump_without_correcting():
    result = validate_price(
        11_000_000,
        same_supplier_history=[80_000_000, 81_000_000, 82_000_000],
        cross_supplier_current=[79_500_000, 80_500_000, 82_000_000],
    )
    assert result.suspicious is True
    assert result.reference_median is not None


def test_price_validation_accepts_normal_market_move():
    result = validate_price(
        79_500_000,
        same_supplier_history=[80_000_000, 81_000_000, 82_000_000],
        cross_supplier_current=[79_000_000, 80_000_000, 82_000_000],
    )
    assert result.suspicious is False
