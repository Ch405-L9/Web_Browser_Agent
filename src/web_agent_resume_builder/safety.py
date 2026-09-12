"""Non-negotiable safety invariants for local application preparation."""

from __future__ import annotations

from web_agent_resume_builder.exceptions import SafetyViolationError
from web_agent_resume_builder.settings import Settings

NO_SUBMIT_STATEMENT = "NO APPLICATION HAS BEEN SUBMITTED. HUMAN REVIEW AND MANUAL SUBMISSION ARE REQUIRED."


def enforce_no_submit(settings: Settings) -> None:
    """Reject any configuration that could enable application submission."""
    if settings.allow_submit is not False:
        raise SafetyViolationError("Submission is permanently disabled.")


def require_interactive_fill_confirmation(
    settings: Settings,
    confirm_fill: bool,
) -> None:
    """Permit field filling only after explicit, safe configuration and confirmation."""
    enforce_no_submit(settings)

    if settings.allow_fill is not True:
        raise SafetyViolationError(
            "ALLOW_FILL must be true before any fill operation is permitted."
        )

    if not confirm_fill:
        raise SafetyViolationError(
            "Field filling requires explicit --confirm-fill confirmation."
        )


def require_resume_upload_disabled(settings: Settings) -> None:
    """Block upload automation during the initial audited implementation."""
    if settings.allow_resume_upload is not False:
        raise SafetyViolationError(
            "Automated résumé upload is disabled in v0.1.0-dev.0."
        )
