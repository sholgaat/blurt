from backend.github_client import _prepare_labels


def test_prepare_labels_merges_tags_and_source_label():
    labels = _prepare_labels(tags=["dev", "product"], metadata={"source": "discord"})
    assert labels == ["dev", "product", "source:discord"]


def test_prepare_labels_handles_empty_inputs():
    labels = _prepare_labels(tags=[], metadata={})
    assert labels == []
