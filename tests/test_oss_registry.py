from hhpi.extraction.oss_registry import discover_oss_engines


def test_registry_is_oss_only():
    engines = {x.engine for x in discover_oss_engines()}
    assert engines == {"tesseract", "paddleocr", "rapidocr", "easyocr"}
