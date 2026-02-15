from backend.llm import ensure_default_tags


def test_ensure_default_tags_returns_existing_tags():
    result = ensure_default_tags(["dev", "product"])
    assert result == ["dev", "product"]


def test_ensure_default_tags_deduplicates():
    result = ensure_default_tags(["dev", "dev", "product"])
    assert result == ["dev", "product"]


def test_ensure_default_tags_inserts_misc_when_empty():
    result = ensure_default_tags([])
    assert result == ["misc"]
