import typer
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from zpools_cli.utils import get_authenticated_client, format_error_response, is_interactive
from zpools._generated.types import UNSET
from zpools_cli.help_scopes import ScopedGroup

app = typer.Typer(help="Manage SSH keys", no_args_is_help=True, cls=ScopedGroup)
console = Console()

def get_key_details(pubkey: str):
    """Calculate fingerprint and comment from public key using ssh-keygen."""
    try:
        with tempfile.NamedTemporaryFile(mode='w+') as f:
            f.write(pubkey)
            f.flush()
            # Output format: <bits> <fingerprint> <comment> (<type>)
            result = subprocess.check_output(['ssh-keygen', '-l', '-f', f.name], stderr=subprocess.STDOUT)
            parts = result.decode('utf-8').strip().split()
            if len(parts) >= 2:
                fingerprint = parts[1]
                comment = " ".join(parts[2:-1]) if len(parts) > 3 else (parts[2] if len(parts) > 2 else "")
                return fingerprint, comment
    except Exception:
        pass
    return "N/A", "N/A"


def _resolve_pubkey_content(raw: str) -> tuple[str, str, str]:
    """
    Resolve input to key content: try as key first, then as path, then fail.
    Returns (pubkey_content, fingerprint, comment). Raises typer.Exit(2) on failure.
    """
    raw = raw.strip()
    if not raw:
        console.print("[red]Error:[/red] No key provided.")
        raise typer.Exit(2)
    fp, comment = get_key_details(raw)
    if fp != "N/A":
        return raw, fp, comment
    p = Path(raw).expanduser()
    if p.is_file():
        content = p.read_text().strip()
        fp2, comment2 = get_key_details(content)
        if fp2 == "N/A":
            console.print(f"[red]Error:[/red] Invalid public key in file: {p}")
            raise typer.Exit(2)
        return content, fp2, comment2
    console.print(f"[red]Error:[/red] Could not parse as public key and file not found: {p}")
    raise typer.Exit(2)

@app.command("list")
def list_sshkeys(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """List all SSH keys."""
    try:
        client = get_authenticated_client(ctx.obj)

        response = client.list_sshkeys()

        if response.status_code == 200:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
                return

            keys = response.parsed.detail.keys
            if not keys:
                console.print("No SSH keys found.")
                return

            table = Table(title="Your SSH Keys")
            table.add_column("ID", style="cyan")
            table.add_column("Fingerprint (from key)", style="magenta")
            table.add_column("Comment (from key)", style="green")

            for key in keys:
                fingerprint = key.additional_properties.get("fingerprint")
                comment = "N/A"

                # If fingerprint missing but we have pubkey, calculate it
                if not fingerprint and key.pubkey:
                    fingerprint, comment = get_key_details(key.pubkey)

                table.add_row(
                    key.pubkey_id,
                    fingerprint or "N/A",
                    comment
                )
            console.print(table)
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(error_msg)
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")

@app.command("add")
def add_sshkey(
    ctx: typer.Context,
    pubkey: Optional[str] = typer.Argument(
        None,
        help="SSH public key path or key string; if omitted user will be prompted interactively",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Add a new SSH key."""
    try:
        client = get_authenticated_client(ctx.obj)

        if pubkey is None:
            if not is_interactive():
                console.print("[red]Error:[/red] No key provided and not in an interactive session. Specify a public key path or run interactively.")
                console.print(ctx.get_help())
                raise typer.Exit(2)
            priv_path = ctx.obj.get("ssh_privkey") if isinstance(ctx.obj, dict) else None
            default_pub_path = str(Path(priv_path).expanduser()) + ".pub" if priv_path else ""
            user_input = typer.prompt(
                "Enter the path or public key to add",
                default=default_pub_path,
            )
            pubkey_content, _fp, _comment = _resolve_pubkey_content(user_input)
        else:
            pubkey_content, _fp, _comment = _resolve_pubkey_content(pubkey)

        response = client.add_sshkey(public_key=pubkey_content)

        if response.status_code == 201:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
                return

            detail = response.parsed.detail
            pubkey_id = getattr(detail, "pubkey_id", UNSET)
            if pubkey_id is UNSET:
                pubkey_id = "N/A"
            console.print("[green]SSH key added successfully![/green]")
            console.print(f"ID: {pubkey_id}")
            console.print(f"Fingerprint (from key): {_fp}")
        elif response.status_code == 409:
            # Key already registered (same key content → same ID)
            try:
                data = json.loads(response.content.decode("utf-8"))
                msg = data.get("message", "SSH key already registered")
                detail = data.get("detail") or {}
                pubkey_id = detail.get("pubkey_id", "N/A")
            except Exception:
                msg = "SSH key already registered"
                pubkey_id = "N/A"
            if json_output:
                print(response.content.decode("utf-8", errors="replace"))
            else:
                console.print(f"[yellow]{msg}[/yellow]")
                console.print(f"ID: {pubkey_id}")
            return
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(error_msg)
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")

@app.command("delete")
def delete_sshkey(
    ctx: typer.Context,
    pubkey_id: str = typer.Argument(..., help="SSH key ID to delete"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Delete an SSH key."""
    if not json_output:
        confirm = typer.confirm(f"Are you sure you want to delete SSH key {pubkey_id}?")
        if not confirm:
            return

    try:
        client = get_authenticated_client(ctx.obj)

        response = client.delete_sshkey(pubkey_id=pubkey_id)

        if response.status_code == 200:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
            else:
                console.print(f"[green]SSH key {pubkey_id} deleted successfully.[/green]")
        elif response.status_code == 404:
            if json_output:
                print(json.dumps({"error": "Not found"}, indent=2))
            else:
                console.print(f"[red]SSH key {pubkey_id} not found.[/red]")
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(error_msg)
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")
