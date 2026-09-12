from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Locator, Page, sync_playwright

from web_agent_resume_builder.browser.interaction_test_policy import reject_submit_attempt
from web_agent_resume_builder.exceptions import SafetyViolationError

FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "synthetic_interaction_form.html"
)


def test_submit_control_is_present_and_disabled() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        try:
            page = context.new_page()
            page.route("**/*", lambda route: route.abort())
            page.set_content(FIXTURE_PATH.read_text(encoding="utf-8"))

            submit = page.locator("#blocked-submit")
            assert submit.count() == 1
            assert submit.get_attribute("type") == "submit"
            assert submit.is_disabled() is True
        finally:
            context.close()
            browser.close()


def test_click_on_submit_control_is_rejected_before_any_browser_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def _spy_click(self: Locator, *args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("click must never be called on a submit control")

    monkeypatch.setattr(Locator, "click", _spy_click)

    with pytest.raises(SafetyViolationError, match="Submission is prohibited"):
        reject_submit_attempt()

    assert calls == [], "Locator.click was invoked; submit-click path was not blocked pre-action"


def test_dom_submit_apis_are_never_invoked(monkeypatch: pytest.MonkeyPatch) -> None:
    """No code path evaluates form.submit() or form.requestSubmit()."""
    calls: list[str] = []

    def _spy_evaluate(self: Page, expression: str, *args: object, **kwargs: object) -> object:
        if "submit" in expression.lower():
            calls.append(expression)
            raise AssertionError("page.evaluate must never invoke a submit API")
        return None

    monkeypatch.setattr(Page, "evaluate", _spy_evaluate)

    with pytest.raises(SafetyViolationError, match="Submission is prohibited"):
        reject_submit_attempt()

    assert calls == [], "page.evaluate was invoked with a submit-related expression"


def test_keyboard_enter_does_not_submit_form() -> None:
    """Defense-in-depth: even a direct Enter-key attempt against the fixture
    produces no request or navigation (fixture's own preventDefault holds)."""
    attempted_requests: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        try:
            page = context.new_page()

            def abort_request(route) -> None:
                attempted_requests.append(route.request.url)
                route.abort()

            page.route("**/*", abort_request)
            page.set_content(FIXTURE_PATH.read_text(encoding="utf-8"))

            page.locator("#test-name").fill("Synthetic Test User")
            page.locator("#test-name").press("Enter")

            assert attempted_requests == []
        finally:
            context.close()
            browser.close()


def test_form_state_invariant_after_forced_click_attempt() -> None:
    """Defense-in-depth: forcing a click on the disabled submit control still
    produces no navigation, request, or preview/state change."""
    attempted_requests: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        try:
            page = context.new_page()

            def abort_request(route) -> None:
                attempted_requests.append(route.request.url)
                route.abort()

            page.route("**/*", abort_request)
            page.set_content(FIXTURE_PATH.read_text(encoding="utf-8"))
            start_url = page.url

            page.locator("#blocked-submit").click(force=True)

            assert attempted_requests == []
            assert page.url == start_url
            assert page.locator("#preview").text_content() == "No values saved"
        finally:
            context.close()
            browser.close()
