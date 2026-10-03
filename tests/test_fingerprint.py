from hhpi.layout.fingerprint import TemplateFingerprint, similarity


def test_template_similarity_identity_and_difference():
    a = TemplateFingerprint((1.0, 0.0, 0.0, 1.0), 1.0, 0.2)
    b = TemplateFingerprint((1.0, 0.0, 0.0, 1.0), 1.0, 0.2)
    c = TemplateFingerprint((0.0, 1.0, 1.0, 0.0), 0.5, 0.05)
    assert similarity(a, b) == 1.0
    assert similarity(a, c) < 0.2
