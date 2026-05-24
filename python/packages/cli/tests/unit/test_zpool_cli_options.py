from typer.testing import CliRunner

from zpools_cli.main import app


runner = CliRunner()


def test_zpool_async_commands_use_watch_option():
    commands = [
        ("create",),
        ("modify", "ZPOOL_ID"),
        ("scrub", "ZPOOL_ID"),
    ]

    for command in commands:
        result = runner.invoke(app, ["zpool", *command, "--help"])

        assert result.exit_code == 0
        assert "--watch" in result.output
        assert "--wait " not in result.output


def test_modify_keeps_wait_until_able_option():
    result = runner.invoke(app, ["zpool", "modify", "ZPOOL_ID", "--help"])

    assert result.exit_code == 0
    assert "--wait-until-able" in result.output
    assert "Wait until cooldown period expires" in result.output


def test_modify_watch_timeout_default_is_longer_than_other_async_commands():
    modify_result = runner.invoke(app, ["zpool", "modify", "ZPOOL_ID", "--help"])
    create_result = runner.invoke(app, ["zpool", "create", "--help"])
    scrub_result = runner.invoke(app, ["zpool", "scrub", "ZPOOL_ID", "--help"])

    assert modify_result.exit_code == 0
    assert create_result.exit_code == 0
    assert scrub_result.exit_code == 0

    assert "43200" in modify_result.output
    assert "1800" in create_result.output
    assert "1800" in scrub_result.output
