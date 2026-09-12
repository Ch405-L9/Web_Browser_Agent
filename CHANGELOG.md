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

[Unreleased]: https://github.com/Ch405-L9/Web_Browser_Agent/compare/dev...HEAD
