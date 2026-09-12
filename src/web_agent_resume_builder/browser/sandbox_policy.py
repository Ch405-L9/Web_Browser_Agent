"""Policy for public, third-party QA/automation practice sandboxes.

These are sites explicitly built and publicly offered by their owners for
automated form-fill/submit practice (e.g. practice-automation.com,
demoqa.com). That is a different, and in this case sufficient, form of
authorization than the "owned staging" requirement in Stage 4 of the
rollout checklist — but it is still domain-gated, and it must never be
allowed to expand toward a real employer/ATS domain such as bluein.green.
That gate (Stage 5) is untouched by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from web_agent_resume_builder.exceptions import SafetyViolationError

# Only add a domain here if the site itself explicitly exists to be
# automated against. Never add a real job board, ATS, or employer domain.
SANDBOX_ALLOWED_DOMAINS: frozenset[str] = frozenset(
    {
        "practice-automation.com",
        "demoqa.com",
        "practice.expandtesting.com",
        "www.roboform.com",
        "www.saucedemo.com",
        "www.way2automation.com",
    }
)

# Domains that must never be reachable through this policy, even by mistake.
SANDBOX_FOREVER_BLOCKED_DOMAINS: frozenset[str] = frozenset({"bluein.green", "www.bluein.green"})


@dataclass(frozen=True)
class SandboxPracticePolicy:
    """Explicit, network-enabled, submit-enabled policy for allowlisted
    public practice sandboxes only."""

    allowed_domains: frozenset[str] = SANDBOX_ALLOWED_DOMAINS
    allow_network: bool = True
    allow_fill: bool = True
    allow_submit: bool = True
    allow_upload: bool = False  # not exercised by this track yet
    pytest_only: bool = True


SANDBOX_PRACTICE_POLICY = SandboxPracticePolicy()


def validate_sandbox_target(url: str, policy: SandboxPracticePolicy = SANDBOX_PRACTICE_POLICY) -> None:
    """Raise SafetyViolationError unless url's host is an allowlisted sandbox
    domain and not a forever-blocked real-site domain."""
    host = urlparse(url).hostname or ""
    if host in SANDBOX_FOREVER_BLOCKED_DOMAINS:
        raise SafetyViolationError(f"{host} is permanently blocked; use the local-mock track instead.")
    if host not in policy.allowed_domains:
        raise SafetyViolationError(f"{host} is not an allowlisted practice sandbox domain.")
    if not policy.pytest_only:
        raise SafetyViolationError("Sandbox policy is restricted to Pytest.")
