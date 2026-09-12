from pathlib import Path

import pytest

from web_agent_resume_builder.jobs.fixture import load_job_fixture


def test_load_job_fixture(tmp_path: Path) -> None:
    (tmp_path / "job.yaml").write_text(
        "title: QA Lead\ncompany: Example Games\n",
        encoding="utf-8",
    )

    fixture = load_job_fixture(tmp_path)

    assert fixture.title == "QA Lead"
    assert fixture.company == "Example Games"
    assert fixture.source_path == tmp_path / "job.yaml"


def test_load_job_fixture_requires_one_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Expected exactly one job YAML fixture"):
        load_job_fixture(tmp_path)
