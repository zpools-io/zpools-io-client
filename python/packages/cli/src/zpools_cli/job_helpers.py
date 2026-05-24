"""Helper functions for job monitoring and resume functionality."""
import json
import typer
from typing import Optional
from rich.console import Console
from zpools_cli.utils import format_error_response
from zpools_cli.job_monitor import wait_for_job_with_progress
from zpools_cli.watch_timeout import exit_watch_timeout
from zpools._generated.types import UNSET

console = Console()


def find_and_resume_job(
    client,
    job_type: str,
    operation_name: str,
    zpool_id: Optional[str] = None,
    timeout: int = 1800,
    json_output: bool = False
):
    """
    Find the most recent job of given type and monitor it to completion.
    
    Args:
        client: Authenticated client
        job_type: Job type to find (e.g., 'zpool_create', 'zpool_scrub', 'zpool_modify')
        operation_name: Human-readable name for progress display (e.g., 'ZPool creation')
        zpool_id: If provided, only match jobs for this specific zpool
        timeout: Max seconds to wait for completion
        json_output: Return JSON vs formatted output
        
    Raises:
        typer.Exit: If no matching job found or job listing fails
    """
    # List jobs to find the most recent job (regardless of state)
    jobs_response = client.list_jobs(limit=100, sort="desc")
    if jobs_response.status_code != 200:
        error_msg = format_error_response(jobs_response.status_code, jobs_response.content, json_output)
        console.print(f"[red]Error fetching jobs:[/red] {error_msg}")
        raise typer.Exit(1)
    
    jobs = jobs_response.parsed.detail.jobs
    matching_job = None
    
    # Find most recent matching job (regardless of state)
    for job in jobs:
        # Get operation type
        operation = job.operation if job.operation is not UNSET else job.additional_properties.get('job_type', "")
        
        # Check job type match
        if operation != job_type:
            continue
        
        # Check zpool_id if needed (for scrub/modify operations)
        if zpool_id:
            parameters = job.additional_properties.get('parameters', '{}')
            try:
                params_dict = json.loads(parameters) if isinstance(parameters, str) else parameters
                job_zpool_id = params_dict.get('zpool_id', '')
                if job_zpool_id != zpool_id:
                    continue
            except:
                continue
        
        # Found matching job (most recent due to sort="desc")
        matching_job = job
        break
    
    if not matching_job:
        if zpool_id:
            error_msg = f"No {job_type} job found for zpool {zpool_id}"
        else:
            error_msg = f"No {job_type} job found"
        
        if json_output:
            print(json.dumps({"error": error_msg}, indent=2))
        else:
            console.print(f"[red]{error_msg}[/red]")
        raise typer.Exit(1)
    
    job_id = matching_job.job_id
    
    # Get current status
    current_status = matching_job.additional_properties.get('current_status', {})
    if isinstance(current_status, dict):
        status_val = current_status.get('state', 'Unknown')
    else:
        status_val = 'Unknown'
    
    # If already completed/failed, just show the result
    if status_val in ('completed', 'failed'):
        if not json_output:
            console.print(f"Job {job_id} already {status_val}")
        
        if json_output:
            # Return the full job details
            print(json.dumps(matching_job.to_dict(), indent=2, default=str))
        else:
            # Show completion message
            msg = current_status.get('message', '') if isinstance(current_status, dict) else ''
            if msg:
                console.print(f"Message: {msg}")
        return matching_job.to_dict() if not json_output else None
    
    # Job is still in progress, monitor it
    if not json_output:
        console.print(f"Resuming monitoring of job: {job_id} (state: {status_val})")
    
    # Monitor the job to completion
    if json_output:
        from zpools.helpers import JobPoller
        try:
            poller = JobPoller(client, job_id, timeout=timeout, poll_interval=10)
            final_job = poller.wait_for_completion()
            print(json.dumps(final_job, indent=2, default=str))
        except TimeoutError:
            exit_watch_timeout(
                console,
                message=f"{operation_name} did not complete before the watch timeout; the job may still be running.",
                json_output=True,
                job_id=job_id,
            )
    else:
        try:
            final_job = wait_for_job_with_progress(
                client, job_id, operation_name, timeout=timeout, poll_interval=5
            )
            return final_job
        except TimeoutError:
            exit_watch_timeout(
                console,
                message=f"{operation_name} did not complete before the watch timeout; the job may still be running.",
                job_id=job_id,
            )
        except RuntimeError:
            console.print(f"Job ID: {job_id}")
            raise typer.Exit(1)
