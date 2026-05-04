from __future__ import annotations

import pytest

from blurt.backend.settings import BackendSettings, validate_github_config


def test_validate_github_config_both_set():
    """Should not raise when both github_token and github_repo are set."""
    settings = BackendSettings(
        github_token="ghp_token123",
        github_repo="owner/repo",
    )
    # Should not raise
    validate_github_config(settings)


def test_validate_github_config_neither_set():
    """Should not raise when both github_token and github_repo are empty."""
    settings = BackendSettings(
        github_token="",
        github_repo="",
    )
    # Should not raise
    validate_github_config(settings)


def test_validate_github_config_only_token_set():
    """Should raise when only github_token is set."""
    settings = BackendSettings(
        github_token="ghp_token123",
        github_repo="",
    )
    with pytest.raises(ValueError, match="Both GITHUB_TOKEN and GITHUB_REPO must be configured together"):
        validate_github_config(settings)


def test_validate_github_config_only_repo_set():
    """Should raise when only github_repo is set."""
    settings = BackendSettings(
        github_token="",
        github_repo="owner/repo",
    )
    with pytest.raises(ValueError, match="Both GITHUB_TOKEN and GITHUB_REPO must be configured together"):
        validate_github_config(settings)


def test_validate_github_config_whitespace_only_treated_as_empty():
    """Should treat whitespace-only values as empty (same as both unset)."""
    settings = BackendSettings(
        github_token="   ",
        github_repo="",
    )
    # Should not raise — both are treated as empty after stripping
    validate_github_config(settings)
