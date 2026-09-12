"""Pytest-only policy for local synthetic interaction safety tests."""

from __future__ import annotations

from dataclasses import dataclass

from web_agent_resume_builder.exceptions import SafetyViolationError

LOCAL_SYNTHETIC_INTERACTION_FIXTURE_ID = "synthetic-interaction-form-v1"
LOCAL_SYNTHETIC_INTERACTION_TARGET = "local://synthetic-interaction-form-v1"


@dataclass(frozen=True)
class LocalSyntheticInteractionTestPolicy:
    """Immutable limits for isolated, local synthetic interaction tests."""

    fixture_id: str = LOCAL_SYNTHETIC_INTERACTION_FIXTURE_ID
    allowed_origins: frozenset[str] = frozenset(
        {LOCAL_SYNTHETIC_INTERACTION_TARGET}
    )
    headed_only: bool = True
    allow_network: bool = False
    allow_fill: bool = True
    allow_upload: bool = False
    allow_submit: bool = False
    allow_artifacts: bool = False
    allow_candidate_data: bool = False
    pytest_only: bool = True


LOCAL_SYNTHETIC_INTERACTION_TEST_POLICY = LocalSyntheticInteractionTestPolicy()


def validate_local_synthetic_interaction_test_policy(
    policy: LocalSyntheticInteractionTestPolicy,
) -> None:
    """Reject any policy that expands the local test-only safety boundary."""
    if policy.fixture_id != LOCAL_SYNTHETIC_INTERACTION_FIXTURE_ID:
        raise SafetyViolationError("Only the approved synthetic fixture is allowed.")

    if policy.allowed_origins != frozenset({LOCAL_SYNTHETIC_INTERACTION_TARGET}):
        raise SafetyViolationError("Only the approved local target is allowed.")

    if not policy.headed_only:
        raise SafetyViolationError("Headed browser mode is mandatory.")

    if policy.allow_network:
        raise SafetyViolationError("Network access is prohibited.")

    if not policy.allow_fill:
        raise SafetyViolationError("Synthetic DOM-only fill is required for this test.")

    if policy.allow_upload:
        raise SafetyViolationError("Uploads are prohibited.")

    if policy.allow_submit:
        raise SafetyViolationError("Submission is prohibited.")

    if policy.allow_artifacts:
        raise SafetyViolationError("Artifacts are prohibited.")

    if policy.allow_candidate_data:
        raise SafetyViolationError("Candidate data access is prohibited.")

    if not policy.pytest_only:
        raise SafetyViolationError("This policy is restricted to Pytest.")


def require_synthetic_fill_allowed(
    policy: LocalSyntheticInteractionTestPolicy,
) -> None:
    """Allow only the approved policy to perform synthetic DOM-only fills."""
    validate_local_synthetic_interaction_test_policy(policy)


def reject_upload_attempt() -> None:
    """Fail closed before any file-selection API can be called."""
    raise SafetyViolationError("File uploads are prohibited in synthetic tests.")


def reject_submit_attempt() -> None:
    """Fail closed before any submit API can be called."""
    raise SafetyViolationError("Submission is prohibited in synthetic tests.")
