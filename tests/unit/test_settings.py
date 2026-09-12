"""Tests for fail-closed application settings."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from web_agent_resume_builder.settings import Settings


def test_allow_submit_must_be_explicitly_false() -> None:
    """Missing ALLOW_SUBMIT is unsafe and must fail."""
    with pytest.raises(ValidationError, match="explicitly set to false"):
        Settings(allow_submit=None)


def test_allow_submit_true_is_rejected() -> None:
    """Enabled submission must fail configuration validation."""
    with pytest.raises(ValidationError, match="explicitly set to false"):
        Settings(allow_submit=True)


def test_allow_submit_false_is_accepted() -> None:
    """Explicit false is the only valid submission configuration."""
    settings = Settings(allow_submit=False)
    assert settings.allow_submit is False


def test_headless_browser_mode_is_rejected() -> None:
    """The implementation requires visible browser operation."""
    with pytest.raises(ValidationError, match="BROWSER_HEADLESS"):
        Settings(allow_submit=False, browser_headless=True)


def test_resume_upload_is_rejected_during_initial_release() -> None:
    """Automated upload must stay disabled during v0.1.0-dev.0."""
    with pytest.raises(ValidationError, match="ALLOW_RESUME_UPLOAD"):
        Settings(allow_submit=False, allow_resume_upload=True)


def test_unapproved_target_host_is_rejected() -> None:
    """Live browsing must remain limited to the approved initial host."""
    with pytest.raises(ValidationError, match="TARGET_APPLICATION_URL host"):
        Settings(
            allow_submit=False,
            target_application_url="https://example.com/application",
        )
