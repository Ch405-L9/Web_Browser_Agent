from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from web_agent_resume_builder.browser.local_mock import (
    LOCAL_MOCK_POLICY,
    inspect_local_mock_application,
)
from web_agent_resume_builder.browser.models import ApplicationReviewArtifact
from web_agent_resume_builder.exceptions import ArtifactError
from web_agent_resume_builder.review.local_mock_artifact import (
    LOCAL_MOCK_ARTIFACT_SCHEMA_VERSION,
    serialize_local_mock_artifact,
)


@pytest.fixture(scope="module")
def safe_artifact() -> ApplicationReviewArtifact:
    return inspect_local_mock_application(LOCAL_MOCK_POLICY)


def _serialized_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(_serialized_keys(child))
        return keys

    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_serialized_keys(child))
        return keys

    return set()


def test_serializes_allowlisted_structural_inventory(
    tmp_path: Path,
    safe_artifact: ApplicationReviewArtifact,
) -> None:
    artifact = safe_artifact
    destination = tmp_path / "inspection" / "inventory.json"

    written_path = serialize_local_mock_artifact(
        artifact,
        destination,
        artifact_root=tmp_path,
    )

    assert written_path == destination
    payload = json.loads(destination.read_text(encoding="utf-8"))

    assert payload["schema_version"] == LOCAL_MOCK_ARTIFACT_SCHEMA_VERSION
    assert payload["artifact_kind"] == "local_mock_form_inventory"
    assert payload["source"] == {
        "kind": "synthetic_local_fixture",
        "target": "local://synthetic-application-fixture",
        "target_domain": "local",
    }
    assert payload["inspection"] == {
        "session_mode": "inspection_only",
        "control_count": 9,
    }
    assert payload["safety"] == {
        "network_blocked": True,
        "fill_blocked": True,
        "upload_blocked": True,
        "submit_blocked": True,
        "application_submitted": False,
        "human_review_required": True,
    }

    assert len(payload["controls"]) == 9
    assert payload["controls"][0]["ordinal"] == 1
    assert payload["controls"][3]["options"] == ["Select one", "Yes", "No"]
    assert sum(control["is_file_input"] for control in payload["controls"]) == 1
    assert sum(control["is_submit_control"] for control in payload["controls"]) == 1


@pytest.mark.parametrize(
    "unsafe_artifact",
    [
        lambda artifact: replace(artifact, target_url="https://example.invalid/form"),
        lambda artifact: replace(artifact, target_domain="remote"),
        lambda artifact: replace(artifact, session_mode="unsafe"),
        lambda artifact: replace(artifact, network_blocked=False),
        lambda artifact: replace(artifact, fill_blocked=False),
        lambda artifact: replace(artifact, upload_blocked=False),
        lambda artifact: replace(artifact, submit_blocked=False),
        lambda artifact: replace(artifact, application_submitted=True),
        lambda artifact: replace(artifact, human_review_required=False),
    ],
)
def test_rejects_unsafe_artifacts(
    tmp_path: Path,
    unsafe_artifact: Callable[
        [ApplicationReviewArtifact],
        ApplicationReviewArtifact,
    ],
    safe_artifact: ApplicationReviewArtifact,
) -> None:
    destination = tmp_path / "inspection" / "inventory.json"

    with pytest.raises(ArtifactError):
        serialize_local_mock_artifact(
            unsafe_artifact(safe_artifact),
            destination,
            artifact_root=tmp_path,
        )

    assert not destination.exists()


@pytest.mark.parametrize(
    "destination",
    [
        Path("/tmp/local_mock_form_inventory.json"),
        Path("../outside-artifacts.json"),
        Path("retrieval/evidence_manifest.json"),
        Path("inspection/inventory.txt"),
    ],
)
def test_rejects_unsafe_destinations(
    tmp_path: Path,
    destination: Path,
    safe_artifact: ApplicationReviewArtifact,
) -> None:
    with pytest.raises(ArtifactError):
        serialize_local_mock_artifact(
            safe_artifact,
            destination,
            artifact_root=tmp_path,
        )


def test_payload_excludes_prohibited_keys_and_content(
    tmp_path: Path,
    safe_artifact: ApplicationReviewArtifact,
) -> None:
    destination = tmp_path / "inspection" / "inventory.json"

    serialize_local_mock_artifact(
        safe_artifact,
        destination,
        artifact_root=tmp_path,
    )

    payload = json.loads(destination.read_text(encoding="utf-8"))
    payload_keys = {key.lower() for key in _serialized_keys(payload)}
    serialized = destination.read_text(encoding="utf-8").lower()

    forbidden_keys = {
        "value",
        "defaultvalue",
        "files",
        "file_path",
        "resume_path",
        "selected_file",
        "checked",
        "selected",
        "cookie",
        "token",
        "password",
        "local_storage",
        "session_storage",
    }

    assert not payload_keys.intersection(forbidden_keys)

    forbidden_content = (
        "/home/",
        "anthony grant",
        "data/candidate",
        "00_ag_applied-ai-engineer_resume.pdf",
    )

    for token in forbidden_content:
        assert token not in serialized
