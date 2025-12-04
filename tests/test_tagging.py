from backend.tagging import ensure_default_tag


def test_ensure_default_tag_returns_existing_tags():
    result = ensure_default_tag(["dev", "product"])
    assert result == ["dev", "product"]


def test_ensure_default_tag_deduplicates():
    result = ensure_default_tag(["dev", "dev", "product"])
    assert result == ["dev", "product"]


def test_ensure_default_tag_inserts_misc_when_empty():
    result = ensure_default_tag([])
    assert result == ["misc"]
