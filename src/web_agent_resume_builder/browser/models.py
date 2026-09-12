"""Safe, inspection-only browser data contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class BrowserSessionPolicy:
    """Policy for a local, synthetic, inspection-only browser session."""

    allowed_origins: frozenset[str] = frozenset()
    headed_only: bool = True
    allow_network: bool = False
    allow_fill: bool = False
    allow_upload: bool = False
    allow_submit: bool = False


@dataclass(frozen=True)
class ScannedFormField:
    """Sanitized structural metadata for one discovered form control."""

    ordinal: int
    label: str
    tag_name: str
    field_type: str
    element_id: str | None
    name: str | None
    required: bool
    disabled: bool
    readonly: bool
    options: tuple[str, ...] = ()
    is_file_input: bool = False
    is_submit_control: bool = False


@dataclass(frozen=True)
class ApplicationReviewArtifact:
    """Read-only inspection output; not authorization for browser interaction."""

    target_url: str
    target_domain: str
    session_mode: Literal["inspection_only"]
    fields: tuple[ScannedFormField, ...] = field(default_factory=tuple)
    network_blocked: bool = True
    fill_blocked: bool = True
    upload_blocked: bool = True
    submit_blocked: bool = True
    application_submitted: bool = False
    human_review_required: bool = True
