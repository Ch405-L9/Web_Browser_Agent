# Changelog

All notable changes to **Web Agent Resume Builder** are documented in this file.

The project follows a release-oriented changelog format. The current development version is `0.1.0.dev0`.

## [Unreleased]

### Added

- Added the global `web-agent` command as the canonical command-line entry point.
- Added the `wab` shorthand command for frequent local operation.
- Retained `web-agent-resume-builder` as a compatibility command so existing installations continue to work.
- Added documented installation instructions for an isolated development environment and an editable global tool installation.
- Added a command reference covering environment checks, candidate validation, retrieval preparation, review draft generation, structured review artifacts, initialization, and version reporting.
- Added a template-safe local job-fixture loader that ignores `*.template.yaml` files and returns no fixture when no completed local fixture is supplied.

### Changed

- Rewrote the project README to accurately describe the current review-only implementation.
- Clarified that application submission, form filling, résumé upload, live job-page scraping, remote API use, external résumé access, and job-fact inference are outside the current safety boundary.
- Documented the required explicit fail-closed configuration, including `ALLOW_SUBMIT=false`, headed browser operation, and disabled résumé upload and form filling.
- Added guidance for extending the agent without weakening the no-submit, no-upload, no-scraping, and no-inference safeguards.
- Preserved the evidence-only review artifact contract and the requirement for human review and manual submission.
- Made template-only job-fixture directories safe for evidence-only workflows without treating templates as factual job data.

### Verification

- Installed the project successfully with the locked dependency set using `uv sync --extra dev`.
- Installed and smoke-tested editable global commands with `uv tool install --editable . --force`.
- Confirmed that `web-agent --help`, `wab --help`, `web-agent doctor`, `wab doctor`, and `web-agent version` operate under the required fail-closed configuration.
- Confirmed that `web-agent candidate validate` validates 18 reviewed atomic evidence records while redacting candidate details in terminal workflows.
- Confirmed that `web-agent review-draft` creates an in-memory structured review artifact with `review_required: true`, `evidence_record_count: 18`, and the required manual-review/no-submission statement.
- Confirmed that `ALLOW_SUBMIT=false`, `ALLOW_FILL=false`, and `ALLOW_RESUME_UPLOAD=false`; doctor reports that a headed browser is required.
- Confirmed the complete test suite passes with `24 passed` in a clean environment.
- Confirmed successful Python compilation and `git diff --check` validation.

### Safety and compatibility

- No application submission capability was added.
- No browser automation, live-page scraping, form filling, résumé upload, remote API fallback, or source résumé access was enabled.
- No candidate data, source documents, generated artifacts, vector stores, patch files, or local hand-off material were added to the tracked change set.
- Human review and manual submission remain required.

### Local mock inspection

- Registered the `inspect-local-mock` CLI command for local, synthetic job-form inspection.
- Added headed Playwright/Chromium rendering for the local synthetic fixture.
- Added read-only detection of form controls, required fields, select controls, file inputs, and submit controls.
- Added terminal reporting for the local inspection result.

### Local mock safety

- Enforced inspection-only behavior for the local mock harness.
- Blocked external network access.
- Blocked field filling, file selection or upload, submit interaction, and application submission.
- Confirmed that the local inspection flow closes the browser after scanning and performs no application action.

### Planned local mock reporting

- Serialize a sanitized local form-inventory review artifact under `artifacts/`.
- Add test coverage for fixture control count, required fields, select options, file inputs, submit controls, unsafe-policy rejection, and artifact safety flags.

### Not included in this milestone

- No live job-application URLs.
- No real application pages.
- No candidate-data entry or field filling.
- No file upload, submission, or application completion capability.

### Local synthetic interaction safety harness

- Added a Pytest-only local synthetic interaction safety harness.
- Added an exact approved synthetic fixture identity and immutable test policy.
- Permitted only hard-coded synthetic DOM-only text, select, and checkbox interactions.
- Enforced blocked network access, upload attempts, submit attempts, artifact capture, and candidate-data access.
- Added explicit exclusions for staging/public URLs, `set_input_files()`, submit APIs, browser-state access, and candidate/resume-derived values.
- Verified with 13 focused synthetic-interaction tests, 39 focused safety tests, and 60 total tests.

### Owned staging fixture

- Documented the self-owned, protected Preview fixture used for controlled Browser Agent staging validation.
- Defined the fixture route as `/badgr_test` on the `test/badgr-apply-fixture` branch of the separate `universal-header-v4` project.
- Recorded synthetic fixture profiles: positive, negative, incomplete, contradictory, verbose, adversarial, and custom.
- Defined runtime-only staging variables for the approved target URL, fixture credentials, network opt-in, and authenticated-staging opt-in.
- Defined Stage 4A as the next Browser Agent milestone: exact-target allowlisting and separately marked opt-in Playwright validation.

### Owned staging security

- Preserved human-in-the-loop, no-auto-submit, no-upload, no-write, and fail-closed boundaries.
- Restricted ordinary CI to offline policy and local-fixture validation.
- Defined the owned Preview fixture as an opt-in staging target only; it is not a production, employer, ATS, job-board, or public-form automation target.
- Required fixture text, including adversarial prompt-injection content, to be treated as untrusted data.
- Prohibited credentials, cookies, authorization headers, Vercel protection tokens, and other secrets from test output or generated artifacts.

[Unreleased]: https://github.com/Ch405-L9/Web_Browser_Agent/compare/dev...HEAD
