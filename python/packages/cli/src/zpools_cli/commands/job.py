import typer
import json
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from zpools_cli.utils import get_authenticated_client, format_error_response, is_interactive, format_timestamp
from zpools_cli.job_monitor import wait_for_job_with_progress
from zpools._generated.api.jobs import (
    get_jobs,
    get_job_job_id,
    get_job_job_id_history
)
from zpools._generated.types import UNSET
from zpools_cli.help_scopes import ScopedGroup

app = typer.Typer(help="Manage background jobs", no_args_is_help=True, cls=ScopedGroup)
console = Console()


def format_relative_time(iso_timestamp: str) -> str:
    """Convert ISO timestamp to compact relative time (e.g. '-2h' or '-1d3h')"""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = now - dt
        
        total_seconds = int(delta.total_seconds())
        days = delta.days
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if days > 0:
            if hours > 0:
                return f"-{days}d{hours}h"
            return f"-{days}d"
        elif hours > 0:
            if minutes > 0:
                return f"-{hours}h{minutes}m"
            return f"-{hours}h"
        elif minutes > 0:
            return f"-{minutes}m"
        else:
            return f"-{seconds}s"
    except:
        return iso_timestamp


@app.command("list")
def list_jobs(
    ctx: typer.Context,
    limit: int = typer.Option(100, "--limit", "-n", help="Maximum number of jobs to return (1-1000)"),
    before: str = typer.Option(None, "--before", help="Jobs created before this date (ISO 8601)"),
    after: str = typer.Option(None, "--after", help="Jobs created after this date (ISO 8601)"),
    sort: str = typer.Option("desc", "--sort", help="Sort order: asc or desc"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """List all background jobs with optional filtering and sorting."""
    try:
        client = get_authenticated_client(ctx.obj)
        
        response = client.list_jobs(limit=limit, before=before, after=after, sort=sort)
        
        if response.status_code == 200:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
                return
            
            jobs = response.parsed.detail.jobs
            if not jobs:
                console.print("No jobs found.")
                return

            table = Table(title="Your Jobs")
            table.add_column("ID", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Status", style="blue")
            table.add_column("Age", style="green", justify="right")
            table.add_column("Message", style="white")

            for job in jobs:
                # API returns fields not in schema - they're in additional_properties
                job_id = job.job_id if job.job_id is not UNSET else ""
                
                # Try schema field first, then additional_properties
                operation = job.operation if job.operation is not UNSET else job.additional_properties.get('job_type', "")
                
                # Status is in current_status.state in additional_properties
                current_status = job.additional_properties.get('current_status', {})
                if isinstance(current_status, dict):
                    status_val = current_status.get('state', 'Unknown')
                    message = current_status.get('message', '')
                else:
                    # Fallback to schema status
                    status_val = job.status.value if job.status is not UNSET else "Unknown"
                    message = ""
                
                # Get created_at (it's a datetime object in the schema)
                if job.created_at is not UNSET:
                    created_at_str = job.created_at.isoformat()
                    relative_time = format_relative_time(created_at_str)
                else:
                    relative_time = ""
                
                # Truncate message if too long
                if len(message) > 50:
                    message = message[:47] + "..."
                
                table.add_row(
                    job_id,
                    operation,
                    status_val,
                    relative_time,
                    message
                )
            console.print(table)
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(error_msg)
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")
            
    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")

@app.command("get")
def get_job(
    ctx: typer.Context,
    job_id: str = typer.Argument(..., help="Job ID to retrieve"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    use_local_tz: bool = typer.Option(False, "--local", help="Show timestamps in local timezone (default: UTC)")
):
    """Get details of a specific job."""
    try:
        client = get_authenticated_client(ctx.obj)
        auth_client = client.get_authenticated_client()
        
        response = get_job_job_id.sync_detailed(job_id=job_id, client=auth_client)
        
        if response.status_code == 200:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
                return
            
            job = response.parsed.detail
            console.print(f"[bold]Job ID:[/bold] {job.id}")
            console.print(f"[bold]Type:[/bold] {job.type}")
            console.print(f"[bold]Status:[/bold] {job.status}")
            console.print(f"[bold]Created At:[/bold] {format_timestamp(job.created_at, use_local_tz)}")
            if job.updated_at:
                console.print(f"[bold]Updated At:[/bold] {format_timestamp(job.updated_at, use_local_tz)}")
            if job.error:
                console.print(f"[red bold]Error:[/red bold] {job.error}")
            if job.result:
                console.print(f"[bold]Result:[/bold] {job.result}")
        elif response.status_code == 404:
            if json_output:
                print(json.dumps({"error": "Not found"}, indent=2))
            else:
                console.print(f"[red]Job {job_id} not found.[/red]")
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(error_msg)
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")

    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")

@app.command("history")
def job_history(
    ctx: typer.Context,
    job_id: str = typer.Argument(..., help="Job ID to get history for"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    watch: bool = typer.Option(False, "--watch", help="Poll job until completion (requires interactive terminal)"),
    timeout: int = typer.Option(1800, "--timeout", help="Maximum time to wait in seconds (only used with --watch)"),
    poll_interval: int = typer.Option(5, "--poll-interval", help="Time between polls in seconds (only used with --watch)"),
    use_local_tz: bool = typer.Option(False, "--local", help="Show timestamps in local timezone (default: UTC)")
):
    """Get history of a specific job."""
    # Validation for --watch flag
    if watch and json_output:
        console.print("[red]Error:[/red] --watch and --json cannot be used together. Use --watch for interactive monitoring or --json for one-time JSON output.")
        raise typer.Exit(1)
    
    if watch and not is_interactive():
        console.print("[red]Error:[/red] --watch requires an interactive terminal. Detected non-interactive session (stdout is not a TTY).")
        raise typer.Exit(1)
    
    try:
        client = get_authenticated_client(ctx.obj)
        auth_client = client.get_authenticated_client()
        
        # If --watch is enabled, use the job monitor
        if watch:
            # First get the job to check its current state and extract job type
            job_response = client.get_job(job_id)
            
            if job_response.status_code == 404:
                console.print(f"[red]Job {job_id} not found.[/red]")
                raise typer.Exit(1)
            elif job_response.status_code != 200:
                error_msg = format_error_response(job_response.status_code, job_response.content, False)
                console.print(f"[red]Error {job_response.status_code}:[/red] {error_msg}")
                raise typer.Exit(1)
            
            # Extract job data from response
            job_data = job_response.parsed.detail.additional_properties.get('job')
            if not job_data:
                console.print(f"[red]Error:[/red] Job {job_id} response missing 'job' field")
                raise typer.Exit(1)
            
            # Get job type for operation name
            operation_name = job_data.get('job_type', 'Job')
            
            # Check current job state
            current_status = job_data.get('current_status', {})
            job_state = current_status.get('state', '')
            message = current_status.get('message', '')
            
            # Handle terminal states
            if job_state == 'succeeded':
                if message:
                    console.print(f"[green]Job {job_id} already succeeded:[/green] {message}")
                else:
                    console.print(f"[green]Job {job_id} already succeeded.[/green]")
                return
            elif job_state == 'failed':
                if message:
                    console.print(f"[red]Job {job_id} already failed:[/red] {message}")
                else:
                    console.print(f"[red]Job {job_id} already failed.[/red]")
                raise typer.Exit(1)
            elif job_state == 'cancelled':
                if message:
                    console.print(f"[yellow]Job {job_id} was cancelled:[/yellow] {message}")
                else:
                    console.print(f"[yellow]Job {job_id} was cancelled.[/yellow]")
                raise typer.Exit(1)
            
            # Job is still running, start watching
            try:
                wait_for_job_with_progress(
                    client, job_id, operation_name,
                    timeout=timeout, poll_interval=poll_interval
                )
            except TimeoutError:
                console.print(f"[red]Timeout waiting for job {job_id} to complete[/red]")
                raise typer.Exit(1)
            except RuntimeError as e:
                # RuntimeError is raised when job fails - message already printed by wait_for_job_with_progress
                raise typer.Exit(1)
            
            return
        
        # Default behavior: show history once
        response = get_job_job_id_history.sync_detailed(job_id=job_id, client=auth_client)
        
        if response.status_code == 200:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
                return
            
            # History is in additional_properties, not in schema fields
            history_data = response.parsed.detail.additional_properties.get('history', [])
            
            if not history_data:
                console.print("No history found for this job.")
                return

            table = Table(title=f"History for Job {job_id}")
            table.add_column("Timestamp", style="green")
            table.add_column("Age", style="cyan", justify="right")
            table.add_column("Status", style="blue")
            table.add_column("Message", style="white")

            for event in history_data:
                timestamp = event.get('timestamp', '')
                event_type = event.get('event_type', '')
                message = event.get('message', '')
                relative_time = format_relative_time(timestamp) if timestamp else ""
                
                table.add_row(
                    format_timestamp(timestamp, use_local_tz),
                    relative_time,
                    event_type,
                    message
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
