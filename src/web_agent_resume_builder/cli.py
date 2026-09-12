"""Command-line interface for local, human-supervised application preparation."""

from __future__ import annotations

import platform
import subprocess

import typer
from rich.console import Console
from rich.table import Table

from web_agent_resume_builder.browser.local_mock import (
    LOCAL_MOCK_POLICY,
    inspect_local_mock_application,
)
from web_agent_resume_builder.candidate.evidence import validate_candidate_data
from web_agent_resume_builder.exceptions import (
    ArtifactError,
    BrowserInspectionError,
    ConfigurationError,
    EvidenceValidationError,
    SafetyViolationError,
)
from web_agent_resume_builder.retrieval.prepare import prepare_retrieval_manifest
from web_agent_resume_builder.safety import NO_SUBMIT_STATEMENT, enforce_no_submit
from web_agent_resume_builder.settings import get_settings
from web_agent_resume_builder.version import INDEX_SCHEMA_VERSION, __version__

app = typer.Typer(
    name="web-agent-resume-builder",
    help="Local-first, human-supervised job-application preparation.",
    no_args_is_help=True,
)
candidate_app = typer.Typer(
    help="Validate local candidate profile and reviewed evidence."
)
retrieval_app = typer.Typer(
    help="Prepare deterministic local retrieval artifacts without embeddings."
)
app.add_typer(candidate_app, name="candidate")
app.add_typer(retrieval_app, name="retrieval")

console = Console()


def git_value(*args: str) -> str:
    """Return Git metadata without failing outside a Git repository."""
    try:
        result = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "unavailable"

    return result.stdout.strip() or "unavailable"


@app.command()
def version() -> None:
    """Print application version and safe runtime configuration."""
    try:
        settings = get_settings()
        enforce_no_submit(settings)
    except ConfigurationError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    table = Table(title="Web Agent Resume Builder")
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Application version", __version__)
    table.add_row("Git commit SHA", git_value("rev-parse", "--short", "HEAD"))
    table.add_row("Git branch", git_value("branch", "--show-current"))
    table.add_row("Active environment", settings.app_env)
    table.add_row("Python version", platform.python_version())
    table.add_row("Playwright version", "resolved at browser-runtime check")
    table.add_row("Ollama host", str(settings.ollama_host))
    table.add_row("Configured generation model", settings.generation_model)
    table.add_row("Configured review model", settings.review_model)
    table.add_row("Configured embedding model", settings.embedding_model)
    table.add_row("Index schema version", INDEX_SCHEMA_VERSION)
    table.add_row("Loaded configuration path", str(settings.loaded_config_path))
    table.add_row("Local artifact root", str(settings.artifact_root))

    console.print(table)
    console.print(f"[bold yellow]{NO_SUBMIT_STATEMENT}[/bold yellow]")


@app.command()
def init() -> None:
    """Create local ignored runtime directories without network activity."""
    settings = get_settings()
    enforce_no_submit(settings)

    for directory in (settings.artifact_root, settings.chroma_path):
        directory.mkdir(parents=True, exist_ok=True)

    console.print("Local runtime directories are ready.")
    console.print(NO_SUBMIT_STATEMENT)


@app.command()
def doctor() -> None:
    """Run non-destructive local configuration and directory checks."""
    settings = get_settings()
    enforce_no_submit(settings)

    for directory in (settings.artifact_root, settings.chroma_path):
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()

    table = Table(title="Doctor Report")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="green")

    table.add_row("Python", platform.python_version())
    table.add_row("Environment", settings.app_env)
    table.add_row("ALLOW_SUBMIT", str(settings.allow_submit))
    table.add_row("ALLOW_FILL", str(settings.allow_fill))
    table.add_row("ALLOW_RESUME_UPLOAD", str(settings.allow_resume_upload))
    table.add_row("Headed browser required", str(not settings.browser_headless))
    table.add_row("Artifact directory", str(settings.artifact_root))
    table.add_row("Chroma directory", str(settings.chroma_path))
    table.add_row("Candidate data directory", str(settings.candidate_data_path))
    table.add_row("Job data directory", str(settings.job_data_path))

    console.print(table)
    console.print(NO_SUBMIT_STATEMENT)


@app.command("inspect-local-mock")
def inspect_local_mock() -> None:
    """Inspect a synthetic local form in a headed, no-action browser session."""
    settings = get_settings()
    enforce_no_submit(settings)

    try:
        artifact = inspect_local_mock_application(LOCAL_MOCK_POLICY)
    except (BrowserInspectionError, SafetyViolationError) as exc:
        console.print(f"[red]Local mock inspection failed:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    table = Table(title="Local Mock Inspection")
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Target", artifact.target_url)
    table.add_row("Session mode", artifact.session_mode)
    table.add_row("Fields detected", str(len(artifact.fields)))
    table.add_row(
        "Upload controls detected",
        str(sum(field.is_file_input for field in artifact.fields)),
    )
    table.add_row(
        "Submit controls detected",
        str(sum(field.is_submit_control for field in artifact.fields)),
    )
    table.add_row("Network", "blocked" if artifact.network_blocked else "unsafe")
    table.add_row("Fill", "blocked" if artifact.fill_blocked else "unsafe")
    table.add_row("Upload", "blocked" if artifact.upload_blocked else "unsafe")
    table.add_row("Submission", "blocked" if artifact.submit_blocked else "unsafe")
    table.add_row(
        "Application submitted",
        "no" if not artifact.application_submitted else "unsafe",
    )

    console.print(table)
    console.print(NO_SUBMIT_STATEMENT)


@candidate_app.command("validate")
def candidate_validate() -> None:
    """Validate local profile and reviewed atomic candidate evidence."""
    settings = get_settings()
    enforce_no_submit(settings)

    try:
        _, records = validate_candidate_data(settings.candidate_data_path)
    except EvidenceValidationError as exc:
        console.print(f"[red]Candidate validation failed:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    console.print(
        "[green]Candidate validation passed.[/green] "
        f"Validated {len(records)} reviewed atomic evidence records."
    )
    console.print("Candidate details are redacted by default in terminal workflows.")
    console.print(NO_SUBMIT_STATEMENT)


@retrieval_app.command("prepare")
def retrieval_prepare() -> None:
    """Build a deterministic local retrieval manifest without embeddings."""
    settings = get_settings()
    enforce_no_submit(settings)

    try:
        result = prepare_retrieval_manifest(
            candidate_data_path=settings.candidate_data_path,
            artifact_root=settings.artifact_root,
        )
    except (ArtifactError, EvidenceValidationError) as exc:
        console.print(f"[red]Retrieval preparation failed:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    console.print("[green]Retrieval preparation completed.[/green]")
    console.print(f"Loaded {result.loaded_record_count} reviewed evidence records.")
    console.print(
        f"Excluded {len(result.excluded_evidence_ids)} non-retrieval guardrail record."
    )
    console.print(
        f"Prepared {result.chunk_count} deterministic chunks from "
        f"{result.included_record_count} index-eligible records."
    )
    console.print(f"Wrote local manifest: {result.manifest_path}")
    console.print(
        "No embedding model, Chroma collection, browser, network request, "
        "upload, form completion, or application submission was invoked."
    )
    console.print(NO_SUBMIT_STATEMENT)


@app.command("draft")
def draft() -> None:
    """Build an in-memory, review-only draft summary from validated evidence."""
    from web_agent_resume_builder.workflow.draft import build_local_draft

    settings = get_settings()
    enforce_no_submit(settings)
    artifact = build_local_draft(settings)

    console.print("[green]Local review draft created in memory.[/green]")
    console.print(f"Validated evidence records: {artifact.evidence_record_count}")
    console.print(f"Status: {artifact.status}")
    console.print(artifact.submission_statement)


@app.command("review-draft")
def review_draft() -> None:
    """Render a structured, in-memory review artifact from local evidence."""
    from web_agent_resume_builder.review.artifact import render_review_artifact
    from web_agent_resume_builder.workflow.draft import build_local_draft

    settings = get_settings()
    enforce_no_submit(settings)

    review = render_review_artifact(build_local_draft(settings))

    console.print("[green]Structured local review artifact created in memory.[/green]")
    console.print_json(data=review)
