"""
PAT scope mapping for CLI help. Used by ScopedGroup to show which PAT scope(s)
each command requires. Empty string = no scope (cell left blank; JWT-only or no API).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

import click

from typer.core import TyperGroup

if TYPE_CHECKING:
    from click import Context, HelpFormatter

# Rich is optional; we use it when Typer uses it for help.
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

# Root keys: "" and "zpcli" so root group works whether invoked as script or as zpcli.
_ROOT_SCOPES = {
    "hello": "",
    "version": "",
    "completion": "",
    "zpool": "zpool",
    "sshkey": "sshkey",
    "pat": "pat",
    "job": "job",
    "billing": "billing",
    "zfs": "",
}

SCOPES_BY_GROUP: dict[str, dict[str, str]] = {
    "": _ROOT_SCOPES,
    "zpcli": _ROOT_SCOPES,
    "zpool": {
        "list": "zpool",
        "create": "zpool, job",
        "delete": "zpool",
        "modify": "zpool, job",
        "expand": "zpool",
        "scrub": "zpool, job",
    },
    "sshkey": {
        "list": "sshkey",
        "add": "sshkey",
        "delete": "sshkey",
    },
    "pat": {
        "list": "pat",
        "create": "",
        "revoke": "pat",
    },
    "job": {
        "list": "job",
        "get": "job",
        "history": "job",
    },
    "billing": {
        "balance": "billing",
        "ledger": "billing",
        "summary": "billing",
        "claim": "",
        "start": "",
    },
    "zfs": {
        "list": "",
        "snapshot": "",
        "destroy": "",
        "recv": "",
        "ssh": "",
    },
}


def _get_scopes_for_group(group_name: str) -> dict[str, str]:
    """Return scope map for this group. Use '' for root when name not in map."""
    return SCOPES_BY_GROUP.get(group_name, SCOPES_BY_GROUP.get("", {}))


def _term_len(s: str) -> int:
    """Length of string for terminal display (avoid full click.formatting import)."""
    try:
        from click._compat import term_len
        return term_len(s)
    except Exception:
        return len(s)


class ScopedGroup(TyperGroup):
    """
    Typer Group that adds a "PAT scope" column to the Commands section of help.
    Uses SCOPES_BY_GROUP for lookup; empty scope leaves the cell blank.
    """

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        commands: Optional[
            Union[dict[str, click.Command], Sequence[click.Command]]
        ] = None,
        rich_markup_mode: Any = None,
        rich_help_panel: Union[str, None] = None,
        suggest_commands: bool = True,
        **attrs: Any,
    ) -> None:
        super().__init__(
            name=name,
            commands=commands,
            rich_markup_mode=rich_markup_mode,
            rich_help_panel=rich_help_panel,
            suggest_commands=suggest_commands,
            **attrs,
        )

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """When Rich is used, call rich_format_help with a patched commands panel that adds PAT scope."""
        from typer import rich_utils

        has_rich = getattr(rich_utils, "HAS_RICH", _HAS_RICH)
        if has_rich and self.rich_markup_mode is not None:
            group_key = ctx.command.name if ctx.command.name in SCOPES_BY_GROUP else ""
            scope_map = _get_scopes_for_group(group_key)
            orig = rich_utils._print_commands_panel

            def _print_commands_panel_with_scope(
                *,
                name: str,
                commands: list,
                markup_mode: Any,
                console: Any,
                cmd_len: int,
            ) -> None:
                if not commands:
                    return
                _make_command_help = getattr(
                    rich_utils,
                    "_make_command_help",
                    lambda **kw: Text(kw.get("help_text", "")),
                )
                STYLE_COMMANDS_TABLE_FIRST_COLUMN = getattr(
                    rich_utils, "STYLE_COMMANDS_TABLE_FIRST_COLUMN", "bold cyan"
                )
                STYLE_COMMANDS_PANEL_BORDER = getattr(
                    rich_utils, "STYLE_COMMANDS_PANEL_BORDER", "dim"
                )
                ALIGN_COMMANDS_PANEL = getattr(rich_utils, "ALIGN_COMMANDS_PANEL", "left")
                DEPRECATED_STRING = getattr(rich_utils, "DEPRECATED_STRING", "(deprecated) ")
                STYLE_DEPRECATED = getattr(rich_utils, "STYLE_DEPRECATED", "red")
                STYLE_DEPRECATED_COMMAND = getattr(
                    rich_utils, "STYLE_DEPRECATED_COMMAND", "dim"
                )

                table = Table(
                    highlight=False,
                    show_header=True,
                    expand=True,
                    box=None,
                )
                table.add_column("Command", style=STYLE_COMMANDS_TABLE_FIRST_COLUMN, no_wrap=True)
                table.add_column("Description", justify="left", no_wrap=False, ratio=10)
                table.add_column("PAT scope", justify="left", no_wrap=True)

                for command in commands:
                    helptext = command.short_help or command.help or ""
                    command_name = command.name or ""
                    scope_str = scope_map.get(command_name, "")
                    if command.deprecated:
                        cmd_text = Text(f"{command_name}", style=STYLE_DEPRECATED_COMMAND)
                        desc_text = Text(DEPRECATED_STRING, style=STYLE_DEPRECATED) + _make_command_help(
                            help_text=helptext, markup_mode=markup_mode
                        )
                    else:
                        cmd_text = Text(command_name)
                        desc_text = _make_command_help(help_text=helptext, markup_mode=markup_mode)
                    table.add_row(cmd_text, desc_text, scope_str)

                if table.row_count:
                    console.print(
                        Panel(
                            table,
                            border_style=STYLE_COMMANDS_PANEL_BORDER,
                            title=name,
                            title_align=ALIGN_COMMANDS_PANEL,
                        )
                    )

            rich_utils._print_commands_panel = _print_commands_panel_with_scope
            try:
                return rich_utils.rich_format_help(
                    obj=self,
                    ctx=ctx,
                    markup_mode=self.rich_markup_mode,
                )
            finally:
                rich_utils._print_commands_panel = orig
        return super().format_help(ctx, formatter)

    def format_commands(self, ctx: "Context", formatter: "HelpFormatter") -> None:
        """Format commands in a 3-column table: Command, Description, PAT scope (non-Rich path)."""
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None or getattr(cmd, "hidden", False):
                continue
            commands.append((subcommand, cmd))

        if not commands:
            return

        group_key = ctx.command.name if ctx.command.name in SCOPES_BY_GROUP else ""
        scope_map = _get_scopes_for_group(group_key)

        # Build rows: (name, short_help, scope)
        limit = formatter.width - 6 - 20  # reserve space for name and scope column
        if limit < 10:
            limit = 50
        rows = []
        for subcommand, cmd in commands:
            help_str = cmd.get_short_help_str(limit)
            scope_str = scope_map.get(subcommand, "")
            rows.append((subcommand, help_str, scope_str))

        # Column widths (name, description, PAT scope)
        name_width = max(_term_len(r[0]) for r in rows)
        scope_width = max(_term_len(r[2]) for r in rows)
        scope_width = max(scope_width, 10)  # header "PAT scope"
        name_width = max(name_width, 4)    # header "Command" / "Name"
        desc_width = max(formatter.width - formatter.current_indent - name_width - scope_width - 4, 10)

        with formatter.section("Commands"):
            # Header row
            header_name = "Command"
            header_desc = "Description"
            header_scope = "PAT scope"
            formatter.write(
                f"{'':>{formatter.current_indent}}{header_name:<{name_width}}  "
                f"{header_desc:<{desc_width}}  {header_scope}\n"
            )
            for name, help_str, scope_str in rows:
                # Truncate description to fit
                if _term_len(help_str) > desc_width:
                    help_str = help_str[: desc_width - 3] + "..."
                formatter.write(
                    f"{'':>{formatter.current_indent}}{name:<{name_width}}  "
                    f"{help_str:<{desc_width}}  {scope_str}\n"
                )
