from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from web_agent_resume_builder.browser.interaction_test_policy import (
    LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY,
    LocalSyntheticInteractionTestPolicy,
    validate_local_synthetic_interaction_test_policy,
)
from web_agent_resume_builder.exceptions import SafetyViolationError

SYNTHETIC_NAME = "Synthetic Test User"
SYNTHETIC_ROLE = "developer"
FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "synthetic_interaction_form.html"
)


@pytest.mark.parametrize(
    "unsafe_policy",
    [
        replace(
            LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY,
            fixture_id="unapproved-fixture",
        ),
        replace(
            LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY,
            allowed_origins=frozenset(),
        ),
        replace(LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY, headed_only=False),
        replace(LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY, allow_network=True),
        replace(LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY, allow_fill=False),
        replace(LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY, allow_upload=True),
        replace(LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY, allow_submit=True),
        replace(LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY, allow_artifacts=True),
        replace(
            LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY,
            allow_candidate_data=True,
        ),
        replace(LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY, pytest_only=False),
    ],
)
def test_policy_rejects_every_expanded_capability(
    unsafe_policy: LocalSyntheticInteractionTestPolicy,
) -> None:
    with pytest.raises(SafetyViolationError):
        validate_local_synthetic_interaction_test_policy(unsafe_policy)


def test_policy_accepts_the_exact_synthetic_test_configuration() -> None:
    validate_local_synthetic_interaction_test_policy(
        LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY
    )


def test_synthetic_values_update_only_the_in_memory_dom_preview() -> None:
    validate_local_synthetic_interaction_test_policy(
        LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY
    )

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

            page.locator("#test-name").fill(SYNTHETIC_NAME)
            page.locator("#test-role").select_option(SYNTHETIC_ROLE)
            page.locator("#test-consent").check()

            assert page.locator("#preview").text_content() == (
                "Synthetic Test User|developer|true"
            )
            assert page.locator("#blocked-submit").is_disabled() is True
            assert page.locator("#blocked-upload").is_disabled() is True
            assert attempted_requests == []
        finally:
            context.close()
            browser.close()
