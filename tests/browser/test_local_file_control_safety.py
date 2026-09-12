from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Locator, sync_playwright

from web_agent_resume_builder.browser.interaction_test_policy import (
    LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY,
    reject_upload_attempt,
    require_synthetic_fill_allowed,
)
from web_agent_resume_builder.exceptions import SafetyViolationError

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "synthetic_interaction_form.html"
)


def test_file_control_is_present_and_classified_prohibited() -> None:
    """The fixture's file control exists but is non-actionable, not actionable."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        try:
            page = context.new_page()
            page.route("**/*", lambda route: route.abort())
            page.set_content(FIXTURE_PATH.read_text(encoding="utf-8"))

            upload = page.locator("#blocked-upload")
            assert upload.count() == 1
            assert upload.get_attribute("type") == "file"
            assert upload.is_disabled() is True
        finally:
            context.close()
            browser.close()


def test_set_input_files_is_rejected_before_any_browser_file_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The policy layer must refuse upload before Locator.set_input_files runs.

    No dummy résumé or file path is created anywhere in this test.
    """
    calls: list[object] = []

    def _spy_set_input_files(self: Locator, *args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("set_input_files must never be called")

    monkeypatch.setattr(Locator, "set_input_files", _spy_set_input_files)

    require_synthetic_fill_allowed(LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY)

    with pytest.raises(SafetyViolationError, match="uploads are prohibited"):
        reject_upload_attempt()

    assert calls == [], "set_input_files was invoked; upload path was not blocked pre-API"


def test_file_control_state_invariant_after_rejected_upload_attempt() -> None:
    """File input stays empty/disabled and no path reaches the DOM preview,
    logs, artifacts, or serializer input."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        try:
            page = context.new_page()
            page.route("**/*", lambda route: route.abort())
            page.set_content(FIXTURE_PATH.read_text(encoding="utf-8"))

            with pytest.raises(SafetyViolationError):
                reject_upload_attempt()

            upload = page.locator("#blocked-upload")
            file_count = upload.evaluate("(el) => el.files.length")
            assert file_count == 0
            assert upload.is_disabled() is True
            assert "resume" not in page.locator("#preview").text_content().lower()
        finally:
            context.close()
            browser.close()
