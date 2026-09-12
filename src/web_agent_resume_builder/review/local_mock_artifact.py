"""Serialize safe, structural local-mock inspection review artifacts."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from web_agent_resume_builder.browser.local_mock import LOCAL_MOCK_TARGET
from web_agent_resume_builder.browser.models import ApplicationReviewArtifact
from web_agent_resume_builder.exceptions import ArtifactError

LOCAL_MOCK_ARTIFACT_SCHEMA_VERSION = "1.0"
DEFAULT_LOCAL_MOCK_ARTIFACT_PATH = Path(
    "artifacts/inspection/local_mock_form_inventory.json"
)
DEFAULT_ARTIFACT_ROOT = Path("artifacts")


def _require_safe_local_mock_artifact(artifact: ApplicationReviewArtifact) -> None:
    """Fail closed unless this is a fully blocked, local inspection result."""
    if artifact.target_url != LOCAL_MOCK_TARGET:
        raise ArtifactError("Artifact target must be the synthetic local fixture.")

    if artifact.target_domain != "local":
        raise ArtifactError("Artifact target domain must be local.")

    if artifact.session_mode != "inspection_only":
        raise ArtifactError("Artifact session mode must be inspection_only.")

    if not artifact.network_blocked:
        raise ArtifactError("Artifact serialization requires blocked network access.")

    if not artifact.fill_blocked:
        raise ArtifactError("Artifact serialization requires blocked field filling.")

    if not artifact.upload_blocked:
        raise ArtifactError("Artifact serialization requires blocked uploads.")

    if not artifact.submit_blocked:
        raise ArtifactError("Artifact serialization requires blocked submission.")

    if artifact.application_submitted:
        raise ArtifactError("Submitted applications must never be serialized.")

    if not artifact.human_review_required:
        raise ArtifactError("Artifact serialization requires human review.")


def _safe_payload(artifact: ApplicationReviewArtifact) -> dict[str, Any]:
    """Build an explicit allowlist-only structural JSON payload."""
    return {
        "schema_version": LOCAL_MOCK_ARTIFACT_SCHEMA_VERSION,
        "artifact_kind": "local_mock_form_inventory",
        "source": {
            "kind": "synthetic_local_fixture",
            "target": artifact.target_url,
            "target_domain": artifact.target_domain,
        },
        "inspection": {
            "session_mode": artifact.session_mode,
            "control_count": len(artifact.fields),
        },
        "safety": {
            "network_blocked": artifact.network_blocked,
            "fill_blocked": artifact.fill_blocked,
            "upload_blocked": artifact.upload_blocked,
            "submit_blocked": artifact.submit_blocked,
            "application_submitted": artifact.application_submitted,
            "human_review_required": artifact.human_review_required,
        },
        "controls": [
            {
                "ordinal": field.ordinal,
                "label": field.label,
                "tag_name": field.tag_name,
                "field_type": field.field_type,
                "element_id": field.element_id,
                "name": field.name,
                "required": field.required,
                "disabled": field.disabled,
                "readonly": field.readonly,
                "options": list(field.options),
                "is_file_input": field.is_file_input,
                "is_submit_control": field.is_submit_control,
            }
            for field in artifact.fields
        ],
    }


def _resolve_destination(
    destination: Path | None,
    artifact_root: Path,
) -> Path:
    """Resolve a destination inside an explicit artifact root."""
    root = Path(artifact_root).resolve()

    if destination is None:
        requested = DEFAULT_LOCAL_MOCK_ARTIFACT_PATH.relative_to(DEFAULT_ARTIFACT_ROOT)
        target = root / requested
    else:
        requested = Path(destination)
        target = requested if requested.is_absolute() else root / requested

    target = target.resolve()

    try:
        relative_target = target.relative_to(root)
    except ValueError as exc:
        raise ArtifactError(
            "Artifact destination must stay inside artifact_root."
        ) from exc

    if not relative_target.parts:
        raise ArtifactError("Artifact destination must name a file.")

    if relative_target.parts[0] == "retrieval":
        raise ArtifactError("Artifact destination must not use artifacts/retrieval/.")

    if target.suffix.lower() != ".json":
        raise ArtifactError("Artifact destination must use a .json suffix.")

    return target


def serialize_local_mock_artifact(
    artifact: ApplicationReviewArtifact,
    destination: Path | None = None,
    *,
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
) -> Path:
    """Validate and atomically write a safe local mock inspection JSON artifact."""
    _require_safe_local_mock_artifact(artifact)
    target = _resolve_destination(destination, artifact_root)

    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _safe_payload(artifact)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            json.dump(payload, temporary_file, indent=2, sort_keys=True)
            temporary_file.write("\n")
            temporary_path = Path(temporary_file.name)

        os.replace(temporary_path, target)
    except OSError as exc:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise ArtifactError(f"Could not write local mock artifact: {exc}") from exc

    return target
