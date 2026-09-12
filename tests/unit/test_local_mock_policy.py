from __future__ import annotations

from dataclasses import replace

import pytest

from web_agent_resume_builder.browser.local_mock import (
    LOCAL_MOCK_POLICY,
    validate_local_mock_policy,
)
from web_agent_resume_builder.exceptions import SafetyViolationError


@pytest.mark.parametrize(
    "unsafe_policy",
    [
        replace(LOCAL_MOCK_POLICY, headed_only=False),
        replace(LOCAL_MOCK_POLICY, allow_network=True),
        replace(LOCAL_MOCK_POLICY, allow_fill=True),
        replace(LOCAL_MOCK_POLICY, allow_upload=True),
        replace(LOCAL_MOCK_POLICY, allow_submit=True),
        replace(LOCAL_MOCK_POLICY, allowed_origins=frozenset()),
    ],
)
def test_local_mock_policy_rejects_unsafe_configuration(unsafe_policy) -> None:
    with pytest.raises(SafetyViolationError):
        validate_local_mock_policy(unsafe_policy)


def test_local_mock_policy_accepts_the_fixed_safe_configuration() -> None:
    validate_local_mock_policy(LOCAL_MOCK_POLICY)
