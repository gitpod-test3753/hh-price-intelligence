from hhpi.extraction.factory import DEFAULT_OSS_ORDER, available_oss_engine_names, build_oss_engine
from hhpi.extraction.tesseract_engine import TesseractEngine


def test_default_order_has_no_cloud_providers():
    assert DEFAULT_OSS_ORDER == ("paddleocr", "rapidocr", "easyocr", "tesseract")


def test_explicit_tesseract_factory():
    engine = build_oss_engine("tesseract", languages="eng")
    assert isinstance(engine, TesseractEngine)


def test_available_names_subset_of_default_order():
    assert set(available_oss_engine_names()) <= set(DEFAULT_OSS_ORDER)
