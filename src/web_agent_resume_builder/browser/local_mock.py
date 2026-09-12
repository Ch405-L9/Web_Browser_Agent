"""Offline, synthetic, inspection-only Playwright harness."""

from __future__ import annotations

from playwright.sync_api import Page, sync_playwright

from web_agent_resume_builder.browser.models import (
    ApplicationReviewArtifact,
    BrowserSessionPolicy,
    ScannedFormField,
)
from web_agent_resume_builder.exceptions import (
    BrowserInspectionError,
    SafetyViolationError,
)

LOCAL_MOCK_TARGET = "local://synthetic-application-fixture"

LOCAL_MOCK_POLICY = BrowserSessionPolicy(
    allowed_origins=frozenset({LOCAL_MOCK_TARGET}),
    headed_only=True,
    allow_network=False,
    allow_fill=False,
    allow_upload=False,
    allow_submit=False,
)

MOCK_APPLICATION_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Synthetic Application Fixture</title>
  </head>
  <body>
    <main>
      <h1>Synthetic Application Fixture</h1>
      <p>This local page is inspection-only. Submission is disabled.</p>

      <form aria-label="Synthetic application form">
        <label for="full-name">Full name</label>
        <input id="full-name" name="full_name" type="text" required>

        <label for="email">Email address</label>
        <input id="email" name="email" type="email" required>

        <label for="experience">Relevant experience</label>
        <textarea id="experience" name="experience" required></textarea>

        <label for="work-authorized">Authorized to work?</label>
        <select id="work-authorized" name="work_authorized" required>
          <option value="">Select one</option>
          <option value="yes">Yes</option>
          <option value="no">No</option>
        </select>

        <fieldset>
          <legend>Preferred contact method</legend>
          <label><input type="radio" name="contact" value="email"> Email</label>
          <label><input type="radio" name="contact" value="phone"> Phone</label>
        </fieldset>

        <label>
          <input id="consent" name="consent" type="checkbox" required>
          I confirm this is synthetic test data.
        </label>

        <label for="resume">Résumé upload</label>
        <input
          id="resume"
          name="resume"
          type="file"
          required
          accept=".pdf,.doc,.docx"
        >

        <button type="submit" disabled aria-disabled="true">
          Submission disabled in local safety fixture
        </button>
      </form>
    </main>
  </body>
</html>
"""


def validate_local_mock_policy(policy: BrowserSessionPolicy) -> None:
    """Reject policies that make the local mock workflow actionable."""
    if not policy.headed_only:
        raise SafetyViolationError("Headed browser mode is mandatory.")

    if policy.allow_network:
        raise SafetyViolationError("Network access is prohibited for local mock mode.")

    if policy.allow_fill:
        raise SafetyViolationError("Form filling is prohibited for local mock mode.")

    if policy.allow_upload:
        raise SafetyViolationError("Uploads are prohibited for local mock mode.")

    if policy.allow_submit:
        raise SafetyViolationError("Application submission is permanently prohibited.")

    if LOCAL_MOCK_TARGET not in policy.allowed_origins:
        raise SafetyViolationError(
            "The synthetic local fixture must be explicitly allowlisted."
        )


def _label_for(page: Page, element_id: str | None, fallback: str) -> str:
    """Return associated label text without reading mutable field values."""
    if element_id:
        label_node = page.locator(f'label[for="{element_id}"]')
        if label_node.count():
            return label_node.first.inner_text().strip()

    return fallback


def inspect_local_mock_application(
    policy: BrowserSessionPolicy = LOCAL_MOCK_POLICY,
) -> ApplicationReviewArtifact:
    """Open a visible synthetic form and return sanitized field metadata."""
    validate_local_mock_policy(policy)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            try:
                page = browser.new_page()
                page.route("**/*", lambda route: route.abort())
                page.set_content(MOCK_APPLICATION_HTML)

                fields: list[ScannedFormField] = []
                locator = page.locator("input, textarea, select, button")

                for index in range(locator.count()):
                    element = locator.nth(index)
                    tag_name = element.evaluate("(node) => node.tagName.toLowerCase()")
                    input_type = element.get_attribute("type") or tag_name
                    element_id = element.get_attribute("id")
                    name = element.get_attribute("name")

                    fallback = element.get_attribute("aria-label") or name or input_type
                    label = _label_for(page, element_id, fallback)

                    options: tuple[str, ...] = ()
                    if tag_name == "select":
                        options = tuple(
                            option.inner_text().strip()
                            for option in element.locator("option").all()
                        )

                    is_file_input = tag_name == "input" and input_type == "file"
                    is_submit_control = (
                        tag_name == "button" and input_type == "submit"
                    ) or (tag_name == "input" and input_type in {"submit", "image"})

                    fields.append(
                        ScannedFormField(
                            ordinal=index + 1,
                            label=label,
                            tag_name=tag_name,
                            field_type=input_type,
                            element_id=element_id,
                            name=name,
                            required=element.get_attribute("required") is not None,
                            disabled=element.is_disabled(),
                            readonly=element.get_attribute("readonly") is not None,
                            options=options,
                            is_file_input=is_file_input,
                            is_submit_control=is_submit_control,
                        )
                    )
            finally:
                browser.close()

    except Exception as exc:
        raise BrowserInspectionError(
            f"Local mock inspection could not complete safely: {exc}"
        ) from exc

    return ApplicationReviewArtifact(
        target_url=LOCAL_MOCK_TARGET,
        target_domain="local",
        session_mode="inspection_only",
        fields=tuple(fields),
        network_blocked=True,
        fill_blocked=True,
        upload_blocked=True,
        submit_blocked=True,
        application_submitted=False,
        human_review_required=True,
    )
