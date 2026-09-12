# Web Agent Resume Builder

A local-first, human-supervised tool for validating approved candidate evidence and preparing review-only application material.

## Safety boundary

The current implementation is deliberately **review-only**. It validates local candidate evidence, prepares deterministic retrieval manifests, and creates in-memory draft and review artifacts. It does not browse live job pages, scrape websites, fill application forms, upload a résumé, access an external résumé symlink, call remote APIs, or submit an application.

> **NO APPLICATION HAS BEEN SUBMITTED. HUMAN REVIEW AND MANUAL SUBMISSION ARE REQUIRED.**

Submission is permanently disabled by the safety contract. Do not weaken the checks or infer job facts from filenames, directories, templates, URLs, or browser pages. A completed local job fixture is optional and is not currently merged into the evidence-only review artifact.

## Installation

The supported runtime is Python 3.12. From a clean checkout, create an isolated environment and install the package with its development dependencies:

```bash
uv sync --extra dev
source .venv/bin/activate
```

For a reusable global command, install the checkout as an editable tool:

```bash
uv tool install --editable .
```

This exposes the canonical command `web-agent` and the shorthand `wab`. The existing `web-agent-resume-builder` command remains supported for compatibility. All three names invoke the same guarded CLI.

## Command reference

Run `web-agent --help` for the live command list. The normal workflow is:

```bash
web-agent doctor                 # non-destructive environment and safety checks
web-agent candidate validate     # validate approved local candidate evidence
web-agent retrieval prepare      # create a deterministic local retrieval manifest
web-agent draft                  # create an in-memory review-only draft
web-agent review-draft           # render the structured review artifact as JSON
web-agent version                # show runtime, configuration, and safety status
```

`init` creates the local ignored runtime directories and performs no network activity:

```bash
web-agent init
```

The shorthand is useful for frequent operation:

```bash
wab doctor
wab draft
```

## Validation

Use the project environment and offline controls when validating changes:

```bash
UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never .venv/bin/python -m compileall -q src
UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never .venv/bin/python -m pytest -q
git diff --check
```

The test suite is configured to enforce a minimum coverage threshold. Do not use broad staging commands such as `git add .`, because local candidate data and generated artifacts are intentionally excluded from the repository.

## Extending the agent safely

Add new behavior behind a small module with explicit unit tests, and route every entry point through `enforce_no_submit`. Preserve the boundaries around no submission, no upload, no unapproved form filling, no live-page scraping, no job-fact inference, and no external résumé access. New job-context fields require an approved completed local fixture schema and a separate review of the artifact contract; do not add them by inference or by treating a template as factual data.

When adding a command, register it in `src/web_agent_resume_builder/cli.py`, document it here, and test both its success path and its safety failure path. When changing configuration, update the environment examples and settings tests. Keep candidate data, source documents, generated artifacts, and local vector stores out of commits.

## Project status

Version `0.1.0.dev0`; development branch: `dev`.
