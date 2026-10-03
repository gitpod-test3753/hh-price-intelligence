from hhpi.catalog.resolver import CatalogItem, CatalogResolver


def test_catalog_exact_alias_and_typo():
    resolver = CatalogResolver(
        [
            CatalogItem(
                canonical_id="xiaomi:redmi_note_15",
                brand="Xiaomi",
                model="Redmi Note 15",
                aliases=("Note 15", "ردمی نوت 15", "N15"),
            )
        ]
    )
    assert resolver.resolve("NOTE 15").canonical_id == "xiaomi:redmi_note_15"
    typo = resolver.resolve("Note 1S", threshold=82)
    assert typo.canonical_id == "xiaomi:redmi_note_15"
