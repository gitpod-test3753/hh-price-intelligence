from hhpi.domain.models import Availability
from hhpi.normalization.color import normalize_color
from hhpi.normalization.price import parse_price
from hhpi.normalization.text import normalize_text
from hhpi.normalization.variant import parse_memory_variant


def test_persian_digits_and_letters():
    assert normalize_text("۲۵۶/۸ مشكي") == "256/8 مشکی"


def test_color_aliases():
    assert normalize_color("مشکی") == "black"
    assert normalize_color("BLK") == "black"
    assert normalize_color("سفید") == "white"


def test_memory_both_orders():
    a = parse_memory_variant("8/256")
    b = parse_memory_variant("256/8")
    assert (a.ram_gb, a.storage_gb) == (8, 256)
    assert (b.ram_gb, b.storage_gb) == (8, 256)


def test_price_scalar():
    p = parse_price("81,000")
    assert p.normalized_toman == 81_000_000
    assert p.availability == Availability.AVAILABLE


def test_price_range():
    p = parse_price("149000-150000")
    assert p.min_toman == 149_000_000
    assert p.max_toman == 150_000_000


def test_price_markers():
    assert parse_price("CALL").availability == Availability.CALL
    assert parse_price("***").availability == Availability.UNPRICED


def test_price_shorthand_range():
    p = parse_price("115000-116")
    assert p.min_toman == 115_000_000
    assert p.max_toman == 116_000_000
