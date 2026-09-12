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

### Changed

- Rewrote the project README to accurately describe the current review-only implementation.
- Clarified that application submission, form filling, résumé upload, live job-page scraping, remote API use, external résumé access, and job-fact inference are outside the current safety boundary.
- Documented the required explicit fail-closed configuration, including `ALLOW_SUBMIT=false`, headed browser operation, and disabled résumé upload and form filling.
- Added guidance for extending the agent without weakening the no-submit, no-upload, no-scraping, and no-inference safeguards.
- Preserved the evidence-only review artifact contract and the requirement for human review and manual submission.

### Verification

- Installed the project successfully with the locked dependency set using `uv sync --extra dev`.
- Installed and smoke-tested the global commands with `uv tool install --editable . --force`.
- Confirmed that `web-agent --help`, `wab --help`, `web-agent doctor`, and `web-agent version` operate under the required fail-closed configuration.
- Confirmed that the test suite passes with `24 passed` in a clean environment.
- Confirmed successful Python compilation and `git diff --check` validation.

### Safety and compatibility

- No application submission capability was added.
- No browser automation, live-page scraping, form filling, résumé upload, remote API fallback, or source résumé access was enabled.
- No candidate data, source documents, generated artifacts, vector stores, or local hand-off material were added to the tracked change set.



[Unreleased]: https://github.com/Ch405-L9/Web_Browser_Agent/compare/dev...HEAD
