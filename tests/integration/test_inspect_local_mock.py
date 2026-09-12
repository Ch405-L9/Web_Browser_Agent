from __future__ import annotations

from web_agent_resume_builder.browser.local_mock import (
    LOCAL_MOCK_POLICY,
    inspect_local_mock_application,
)


def test_local_mock_inspection_returns_sanitized_structural_inventory() -> None:
    artifact = inspect_local_mock_application(LOCAL_MOCK_POLICY)

    assert artifact.target_url == "local://synthetic-application-fixture"
    assert artifact.target_domain == "local"
    assert artifact.session_mode == "inspection_only"

    assert artifact.network_blocked is True
    assert artifact.fill_blocked is True
    assert artifact.upload_blocked is True
    assert artifact.submit_blocked is True
    assert artifact.application_submitted is False
    assert artifact.human_review_required is True

    assert len(artifact.fields) == 9
    assert [field.ordinal for field in artifact.fields] == list(range(1, 10))

    assert sum(field.required for field in artifact.fields) == 6
    assert sum(field.is_file_input for field in artifact.fields) == 1
    assert sum(field.is_submit_control for field in artifact.fields) == 1

    authorization = next(
        field for field in artifact.fields if field.name == "work_authorized"
    )
    assert authorization.tag_name == "select"
    assert authorization.options == ("Select one", "Yes", "No")

    resume = next(field for field in artifact.fields if field.is_file_input)
    assert resume.name == "resume"
    assert resume.required is True
    assert resume.options == ()

    submit_control = next(field for field in artifact.fields if field.is_submit_control)
    assert submit_control.tag_name == "button"
    assert submit_control.disabled is True

    for field in artifact.fields:
        assert not hasattr(field, "value")
        assert not hasattr(field, "default_value")
        assert not hasattr(field, "file_path")
        assert not hasattr(field, "selected_file")
        assert not hasattr(field, "selector")
