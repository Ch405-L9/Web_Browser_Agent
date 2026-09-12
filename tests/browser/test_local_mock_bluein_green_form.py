from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "mock_bluein_green_application_form.html"
)


def test_mock_form_structure_matches_expected_generic_fields() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        try:
            page = context.new_page()
            page.route("**/*", lambda route: route.abort())
            page.set_content(FIXTURE_PATH.read_text(encoding="utf-8"))

            expected_ids = [
                "mock-full-name",
                "mock-email",
                "mock-phone",
                "mock-portfolio",
                "mock-experience",
                "mock-work-auth",
                "mock-cover-letter",
                "mock-resume",
                "mock-consent",
            ]
            for field_id in expected_ids:
                assert page.locator(f"#{field_id}").count() == 1, field_id
        finally:
            context.close()
            browser.close()


def test_mock_form_resume_and_submit_controls_are_disabled() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        try:
            page = context.new_page()
            page.route("**/*", lambda route: route.abort())
            page.set_content(FIXTURE_PATH.read_text(encoding="utf-8"))

            resume = page.locator("#mock-resume")
            submit = page.locator("#mock-submit")
            assert resume.get_attribute("type") == "file"
            assert resume.is_disabled() is True
            assert submit.get_attribute("type") == "submit"
            assert submit.is_disabled() is True
        finally:
            context.close()
            browser.close()


def test_mock_form_never_issues_a_network_request() -> None:
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

            page.locator("#mock-full-name").fill("Synthetic Test User")
            page.locator("#mock-email").fill("synthetic@example.invalid")
            page.locator("#mock-experience").select_option("2-4")
            page.locator("#mock-consent").check()

            assert page.locator("#mock-preview").text_content() == (
                "Synthetic Test User|synthetic@example.invalid|2-4|true"
            )
            assert attempted_requests == []
        finally:
            context.close()
            browser.close()
