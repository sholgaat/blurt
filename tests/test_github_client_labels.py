from blurt.backend.github_client import _prepare_labels


def test_prepare_labels_merges_tags_and_source_label_discord():
    labels = _prepare_labels(tags=["dev", "product"], metadata={"source": "discord"})
    assert labels == ["dev", "product", "source:discord"]


def test_prepare_labels_merges_tags_and_source_label_telegram():
    labels = _prepare_labels(tags=["dev", "product"], metadata={"source": "telegram"})
    assert labels == ["dev", "product", "source:telegram"]


def test_prepare_labels_handles_empty_inputs():
    labels = _prepare_labels(tags=[], metadata={})
    assert labels == []


def test_prepare_labels_no_source_label_for_empty_source():
    labels = _prepare_labels(tags=["dev"], metadata={"source": ""})
    assert labels == ["dev"]
