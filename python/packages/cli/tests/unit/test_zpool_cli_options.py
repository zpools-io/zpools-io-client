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
