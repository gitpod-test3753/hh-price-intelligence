from hhpi.extraction.tesseract_passes import DEFAULT_TESSERACT_PASSES


def test_tesseract_passes_cover_mixed_sparse_and_grid_removed():
    ids = {p.pass_id for p in DEFAULT_TESSERACT_PASSES}
    assert {"mixed_block", "mixed_sparse", "english_block", "mixed_grid_removed"} <= ids
