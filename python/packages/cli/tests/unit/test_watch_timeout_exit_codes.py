from types import SimpleNamespace

from typer.testing import CliRunner

from zpools_cli.commands import job as job_command
from zpools_cli.commands import zpool as zpool_command
from zpools_cli.main import app


runner = CliRunner()


class FakeCreateClient:
    def create_zpool(self, size_gib: int, volume_type: str):
        return SimpleNamespace(
            status_code=202,
            parsed=SimpleNamespace(
                detail=SimpleNamespace(job_id="job-create"),
                to_dict=lambda: {"detail": {"job_id": "job-create"}},
            ),
        )


class FakeScrubClient:
    def scrub_zpool(self, zpool_id: str):
        return SimpleNamespace(
            status_code=202,
            parsed=SimpleNamespace(
                detail=SimpleNamespace(job_id="job-scrub"),
                to_dict=lambda: {"detail": {"job_id": "job-scrub"}},
            ),
        )


class FakeJobClient:
    def get_authenticated_client(self):
        return SimpleNamespace()

    def get_job(self, job_id: str):
        return SimpleNamespace(
            status_code=200,
            parsed=SimpleNamespace(
                detail=SimpleNamespace(
                    additional_properties={
                        "job": {
                            "job_type": "zpool_create",
                            "current_status": {"state": "running"},
                        }
                    }
                )
            ),
        )


def write_rcfile(tmp_path):
    rcfile = tmp_path / "zpoolrc"
    rcfile.write_text("ZPOOLPAT=test-token\n")
    return rcfile


def raise_timeout(*args, **kwargs):
    raise TimeoutError("Operation did not complete within timeout")


def test_create_watch_timeout_has_distinct_exit_code(monkeypatch, tmp_path):
    rcfile = write_rcfile(tmp_path)
    monkeypatch.setattr(zpool_command, "get_authenticated_client", lambda config: FakeCreateClient())
    monkeypatch.setattr(zpool_command, "wait_for_job_with_progress", raise_timeout)

    result = runner.invoke(app, ["--rcfile", str(rcfile), "zpool", "create", "--watch"])

    assert result.exit_code == 3
    assert "Watch timed out" in result.output
    assert "Job ID: job-create" in result.output


def test_scrub_watch_timeout_has_distinct_exit_code(monkeypatch, tmp_path):
    rcfile = write_rcfile(tmp_path)
    monkeypatch.setattr(zpool_command, "get_authenticated_client", lambda config: FakeScrubClient())
    monkeypatch.setattr(zpool_command, "wait_for_job_with_progress", raise_timeout)

    result = runner.invoke(app, ["--rcfile", str(rcfile), "zpool", "scrub", "ZPOOL_ID", "--watch"])

    assert result.exit_code == 3
    assert "Watch timed out" in result.output
    assert "Job ID: job-scrub" in result.output


def test_job_history_watch_timeout_has_distinct_exit_code(monkeypatch, tmp_path):
    rcfile = write_rcfile(tmp_path)
    monkeypatch.setattr(job_command, "is_interactive", lambda: True)
    monkeypatch.setattr(job_command, "get_authenticated_client", lambda config: FakeJobClient())
    monkeypatch.setattr(job_command, "wait_for_job_with_progress", raise_timeout)

    result = runner.invoke(app, ["--rcfile", str(rcfile), "job", "history", "job-create", "--watch"])

    assert result.exit_code == 3
    assert "Watch timed out" in result.output
    assert "Job ID: job-create" in result.output
