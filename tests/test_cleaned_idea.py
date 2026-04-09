import pytest
from pydantic import ValidationError

from backend.llm.base import CleanedIdea


def test_tags_are_lowercased():
    result = CleanedIdea(title="Title", summary="Summary", tags=["Dev", "DevOps"])
    assert result.tags == ["dev", "devops"]


def test_tags_are_deduplicated():
    result = CleanedIdea(title="Title", summary="Summary", tags=["dev", "DEV", "dev"])
    assert result.tags == ["dev"]


def test_tags_fallback_to_misc_when_empty():
    result = CleanedIdea(title="Title", summary="Summary", tags=[])
    assert result.tags == ["misc"]


def test_tags_filter_empty_strings():
    result = CleanedIdea(title="Title", summary="Summary", tags=["", "dev"])
    assert result.tags == ["dev"]


def test_blank_title_raises_validation_error():
    with pytest.raises(ValidationError):
        CleanedIdea(title="", summary="Summary", tags=["dev"])


def test_whitespace_title_raises_validation_error():
    with pytest.raises(ValidationError):
        CleanedIdea(title="   ", summary="Summary", tags=["dev"])


def test_blank_summary_raises_validation_error():
    with pytest.raises(ValidationError):
        CleanedIdea(title="Title", summary="", tags=["dev"])


def test_title_and_summary_are_stripped():
    result = CleanedIdea(title="  Title ", summary=" Summary  ", tags=["dev"])
    assert result.title == "Title"
    assert result.summary == "Summary"


def test_model_validate_from_dict_normalizes_tags():
    result = CleanedIdea.model_validate(
        {"title": "Title", "summary": "Summary", "tags": ["Dev", "DEV"]}
    )
    assert result.tags == ["dev"]


def test_model_validate_missing_field_raises_validation_error():
    with pytest.raises(ValidationError):
        CleanedIdea.model_validate({"title": "Title", "tags": ["dev"]})
