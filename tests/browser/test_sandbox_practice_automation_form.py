from __future__ import annotations

import os

import pytest
from playwright.sync_api import sync_playwright

from web_agent_resume_builder.browser.sandbox_policy import (
    SANDBOX_PRACTICE_POLICY,
    validate_sandbox_target,
)

TARGET_URL = "https://practice-automation.com/form-fields/"

# Real network egress to a third party. Off by default; opt in explicitly:
#   ALLOW_SANDBOX_NETWORK=1 uv run pytest -q tests/browser/test_sandbox_practice_automation_form.py
requires_sandbox_network = pytest.mark.skipif(
    os.environ.get("ALLOW_SANDBOX_NETWORK") != "1",
    reason="Set ALLOW_SANDBOX_NETWORK=1 to run tests against a real public sandbox site.",
)


def test_policy_rejects_bluein_green_permanently() -> None:
    from web_agent_resume_builder.exceptions import SafetyViolationError

    with pytest.raises(SafetyViolationError):
        validate_sandbox_target("https://www.bluein.green/jobs/games-qa-qc-lead/apply/")


def test_policy_rejects_non_allowlisted_domain() -> None:
    from web_agent_resume_builder.exceptions import SafetyViolationError

    with pytest.raises(SafetyViolationError):
        validate_sandbox_target("https://example.com/some-form/")


@requires_sandbox_network
def test_fill_and_submit_practice_automation_form_fields() -> None:
    validate_sandbox_target(TARGET_URL, SANDBOX_PRACTICE_POLICY)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        try:
            page = context.new_page()
            page.goto(TARGET_URL, wait_until="domcontentloaded")

            form = page.locator("form").first

            form.get_by_label("Name", exact=False).first.fill("Sandbox Test User")
            form.get_by_label("Password", exact=False).first.fill("Sandb0x-Test-Only!")
            form.get_by_label("Email", exact=False).first.fill("sandbox-test@example.invalid")
            form.get_by_label("Message", exact=False).first.fill("Automated sandbox practice run.")

            page.locator("#drink3").check()
            form.get_by_role("radio", name="Blue").check()

            dropdown = form.get_by_role("combobox").first
            dropdown.select_option(label="Yes")

            assert form.get_by_label("Name", exact=False).first.input_value() == "Sandbox Test User"
            assert page.locator("#drink3").is_checked()
            assert form.get_by_role("radio", name="Blue").is_checked()
            assert dropdown.input_value() == "yes"

            # SUBMIT IS INTENTIONALLY NOT CALLED YET.
            # Uncomment only after an explicit go-ahead on this specific run:
            # form.get_by_role("button", name="Submit").click()
        finally:
            context.close()
            browser.close()
