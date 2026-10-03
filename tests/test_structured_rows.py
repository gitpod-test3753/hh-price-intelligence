from hhpi.extraction.structured_rows import _network, _repair_digit_context
from hhpi.normalization.variant import parse_memory_variant


def test_repair_s_as_five_in_memory_context():
    repaired = _repair_digit_context("NOTE15 PRO S12/12 4G")
    assert "512/12" in repaired
    memory = parse_memory_variant(repaired)
    assert memory.ram_gb == 12
    assert memory.storage_gb == 512


def test_network_from_compact_ocr_text():
    assert _network("NOTE15PRO 512/12 4G") == "4G"
    assert _network("A56 8/256 5G") == "5G"


def test_memory_parser_handles_network_glued_to_ram():
    from hhpi.extraction.structured_rows import _strip_network_suffix
    repaired = _repair_digit_context("INOTE1SPROS12/124G")
    memory = parse_memory_variant(_strip_network_suffix(repaired))
    assert memory.storage_gb == 512
    assert memory.ram_gb == 12


def test_memory_parser_uses_valid_suffix_when_model_digits_are_glued():
    memory = parse_memory_variant("POCOC7164/4")
    assert memory.storage_gb == 64
    assert memory.ram_gb == 4
