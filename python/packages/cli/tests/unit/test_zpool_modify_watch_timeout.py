from types import SimpleNamespace

from typer.testing import CliRunner

from zpools_cli.commands import zpool as zpool_command
from zpools_cli.main import app


runner = CliRunner()


class FakeClient:
    def modify_zpool(self, zpool_id: str, target_volume_type: str):
        assert zpool_id == "fall-become-lucky-difficult"
        assert target_volume_type == "sc1"
        return SimpleNamespace(status_code=202, parsed=None)


def test_modify_watch_timeout_has_distinct_exit_code_and_guidance(monkeypatch, tmp_path):
    rcfile = tmp_path / "zpoolrc"
    rcfile.write_text("ZPOOLPAT=test-token\n")

    def raise_timeout(client, zpool_id, timeout, poll_interval):
        assert zpool_id == "fall-become-lucky-difficult"
        raise TimeoutError("Operation did not complete within timeout")

    monkeypatch.setattr(zpool_command, "get_authenticated_client", lambda config: FakeClient())
    monkeypatch.setattr(zpool_command, "wait_for_modify_with_progress", raise_timeout)

    result = runner.invoke(
        app,
        [
            "--rcfile",
            str(rcfile),
            "zpool",
            "modify",
            "fall-become-lucky-difficult",
            "--type",
            "sc1",
            "--watch",
        ],
    )

    assert result.exit_code == 3
    assert "Watch timed out" in result.output
    assert "EBS modification may still be running" in result.output
    assert "zpcli zpool modify fall-become-lucky-difficult --resume" in result.output


def test_modify_json_watch_timeout_has_distinct_exit_code(monkeypatch, tmp_path):
    rcfile = tmp_path / "zpoolrc"
    rcfile.write_text("ZPOOLPAT=test-token\n")

    def raise_timeout():
        raise TimeoutError("Operation did not complete within timeout")

    monkeypatch.setattr(zpool_command, "get_authenticated_client", lambda config: FakeClient())
    monkeypatch.setattr(
        "zpools.helpers.ModifyPoller.wait_for_completion",
        lambda self: raise_timeout(),
    )

    result = runner.invoke(
        app,
        [
            "--rcfile",
            str(rcfile),
            "zpool",
            "modify",
            "fall-become-lucky-difficult",
            "--type",
            "sc1",
            "--watch",
            "--json",
        ],
    )

    assert result.exit_code == 3
    assert '"error": "watch_timeout"' in result.output
    assert "EBS modification may still be running" in result.output
