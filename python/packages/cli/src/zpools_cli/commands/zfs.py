import typer
import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from zpools_cli.utils import get_ssh_client
from zpools_cli.help_scopes import ScopedGroup

app = typer.Typer(help="ZFS operations over SSH", no_args_is_help=True, cls=ScopedGroup)
console = Console()

def get_ssh_config(client, username):
    """Extract SSH configuration from client and config."""
    if not client.ssh_host:
        console.print("[red]Error:[/red] SSH_HOST not configured. Set in ~/.config/zpools.io/zpoolrc or export SSH_HOST")
        raise typer.Exit(1)
    
    if not client.ssh_privkey:
        console.print("[red]Error:[/red] SSH_PRIVKEY_FILE not configured. Set in ~/.config/zpools.io/zpoolrc or export SSH_PRIVKEY_FILE")
        raise typer.Exit(1)
    
    privkey_path = Path(client.ssh_privkey)
    if not privkey_path.exists():
        console.print(f"[red]Error:[/red] SSH private key not found: {privkey_path}")
        raise typer.Exit(1)
    
    if not username:
        console.print("[red]Error:[/red] ZPOOL_USER not configured. Set in ~/.config/zpools.io/zpoolrc or export ZPOOL_USER")
        raise typer.Exit(1)
    
    return client.ssh_host, str(privkey_path), username

def ssh_exec(ssh_host: str, privkey: str, username: str, command: List[str], pipe_stdin: bool = False):
    """Execute command via SSH."""
    ssh_cmd = [
        "ssh", "-i", privkey,
        f"{username}@{ssh_host}"
    ] + command
    
    if pipe_stdin:
        # For recv operation, pass stdin through
        result = subprocess.run(ssh_cmd, stdin=sys.stdin)
        return result.returncode
    else:
        result = subprocess.run(ssh_cmd)
        return result.returncode

@app.command()
def list(
    ctx: typer.Context,
    dataset: str = typer.Argument(..., help="Dataset to list"),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="List recursively")
):
    """List ZFS datasets."""
    try:
        client = get_ssh_client(ctx.obj)
        ssh_host, privkey, username = get_ssh_config(client, ctx.obj["username"])
        
        cmd = ["zfs", "list"]
        if recursive:
            cmd.append("-r")
        cmd.append(dataset)
        
        exit_code = ssh_exec(ssh_host, privkey, username, cmd)
        if exit_code != 0:
            raise typer.Exit(exit_code)
        
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@app.command()
def snapshot(
    ctx: typer.Context,
    snapshot: str = typer.Argument(..., help="Snapshot name (dataset@snapname)")
):
    """Create a ZFS snapshot."""
    try:
        client = get_ssh_client(ctx.obj)
        ssh_host, privkey, username = get_ssh_config(client, ctx.obj["username"])
        
        cmd = ["zfs", "snapshot", snapshot]
        exit_code = ssh_exec(ssh_host, privkey, username, cmd)
        if exit_code != 0:
            raise typer.Exit(exit_code)
        
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@app.command()
def destroy(
    ctx: typer.Context,
    dataset: str = typer.Argument(..., help="Dataset or snapshot to destroy"),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Destroy recursively")
):
    """Destroy a ZFS dataset or snapshot."""
    try:
        client = get_ssh_client(ctx.obj)
        ssh_host, privkey, username = get_ssh_config(client, ctx.obj["username"])
        
        cmd = ["zfs", "destroy"]
        if recursive:
            cmd.append("-r")
        cmd.append(dataset)
        
        exit_code = ssh_exec(ssh_host, privkey, username, cmd)
        if exit_code != 0:
            raise typer.Exit(exit_code)
        
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@app.command()
def recv(
    ctx: typer.Context,
    dataset: str = typer.Argument(..., help="Target dataset"),
    force: bool = typer.Option(False, "-F", "--force", help="Force rollback")
):
    """
    Receive a ZFS stream from stdin.
    
    Example: zfs send localpool/ds@snap | zpcli zfs recv remotepool/ds
    """
    try:
        client = get_ssh_client(ctx.obj)
        ssh_host, privkey, username = get_ssh_config(client, ctx.obj["username"])
        
        cmd = ["zfs", "recv"]
        if force:
            cmd.append("-F")
        cmd.append(dataset)
        
        exit_code = ssh_exec(ssh_host, privkey, username, cmd, pipe_stdin=True)
        if exit_code != 0:
            raise typer.Exit(exit_code)
        
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

@app.command(
    context_settings={
        "allow_interspersed_args": False,
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    }
)
def ssh(
    ctx: typer.Context,
):
    """
    Open SSH connection or run command on remote host.
    
    Examples:
      zpcli zfs ssh                         # Interactive shell
      zpcli zfs ssh zfs list                # Run command
      zpcli zfs ssh zfs list -t filesystem  # Flags are passed through
    """
    try:
        # Get all remaining args from context
        command = ctx.args if ctx.args else []
        
        client = get_ssh_client(ctx.obj)
        ssh_host, privkey, username = get_ssh_config(client, ctx.obj["username"])
        
        exit_code = ssh_exec(ssh_host, privkey, username, command, pipe_stdin=False)
        if exit_code != 0:
            raise typer.Exit(exit_code)
        
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
