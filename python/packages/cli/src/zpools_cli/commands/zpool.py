import typer
import json
import time
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from zpools_cli.utils import get_authenticated_client, format_error_response, format_timestamp
from zpools_cli.cooldown import calculate_cooldown_info
from zpools_cli.job_monitor import wait_for_job_with_progress
from zpools_cli.job_helpers import find_and_resume_job
from zpools_cli.volume_monitor import wait_for_modify_with_progress
from zpools_cli.wait_helpers import wait_with_token_refresh
from zpools._generated.api.zpools import (
    get_zpools,
    post_zpool,
    delete_zpool_zpool_id,
    post_zpool_zpool_id_modify,
    post_zpool_zpool_id_scrub
)
from zpools._generated.models.post_zpool_body import PostZpoolBody
from zpools._generated.models.post_zpool_body_new_size_in_gib import PostZpoolBodyNewSizeInGib
from zpools._generated.models.post_zpool_body_volume_type import PostZpoolBodyVolumeType
from zpools._generated.models.post_zpool_zpool_id_modify_body import PostZpoolZpoolIdModifyBody
from zpools._generated.models.post_zpool_zpool_id_modify_body_volume_type import PostZpoolZpoolIdModifyBodyVolumeType
from zpools._generated.types import UNSET
from zpools_cli.help_scopes import ScopedGroup

app = typer.Typer(help="Manage ZFS pools", no_args_is_help=True, cls=ScopedGroup)
console = Console()


@app.command("list")
def list_zpools(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """List all ZPools."""
    try:
        client = get_authenticated_client(ctx.obj)
        auth_client = client.get_authenticated_client()
        
        response = get_zpools.sync_detailed(client=auth_client)
        
        if response.status_code == 200:
            if json_output:
                # Convert response to dict safely, handling nested objects
                try:
                    result = response.parsed.to_dict()
                    print(json.dumps(result, indent=2, default=str))
                except Exception as e:
                    # Fallback: manually build the dict structure
                    zpools_list = []
                    for pool in response.parsed.detail.zpools:
                        pool_dict = {
                            'zpool_id': pool.zpool_id if pool.zpool_id is not UNSET else None,
                            'name': pool.name if pool.name is not UNSET else None,
                            'size_gb': pool.size_gb if pool.size_gb is not UNSET else None,
                            'status': pool.status if pool.status is not UNSET else None,
                            'created_at': str(pool.created_at) if pool.created_at is not UNSET else None,
                        }
                        pool_dict.update(pool.additional_properties)
                        zpools_list.append(pool_dict)
                    print(json.dumps({'detail': {'zpools': zpools_list}, 'message': response.parsed.message}, indent=2, default=str))
                return

            zpools = response.parsed.detail.zpools
            if not zpools or not zpools.additional_properties:
                console.print("No ZPools found.")
                return

            # Display zpools - iterate and show each with its volumes
            for zpool_id, pool in zpools.additional_properties.items():
                # Get zpool-level info from SDK attributes
                username = pool.username if pool.username is not UNSET else 'N/A'
                volume_count = pool.volume_count if pool.volume_count is not UNSET else 0
                create_time = pool.create_time if pool.create_time is not UNSET else None
                last_scrub = pool.last_scrub_time if pool.last_scrub_time is not UNSET else None
                
                # Format dates
                create_time_str = create_time.strftime('%Y-%m-%d') if create_time else 'N/A'
                last_scrub_str = last_scrub.strftime('%Y-%m-%d') if last_scrub else 'Never'
                
                console.print(f"\n[bold cyan]ZPool:[/bold cyan] {zpool_id}")
                console.print(f"  User: {username}  |  Volumes: {volume_count}  |  Created: {create_time_str}  |  Last Scrub: {last_scrub_str}")
                
                # Get volumes from SDK attribute
                volumes = pool.volumes if pool.volumes is not UNSET else []
                
                if not volumes:
                    console.print("  [yellow]No volumes found[/yellow]")
                    continue
                
                # Create table for this zpool's volumes
                vol_table = Table(show_header=True, box=None, padding=(0, 2))
                vol_table.add_column("Size (GiB)", style="green")
                vol_table.add_column("Type", style="magenta")
                vol_table.add_column("State", style="yellow")
                vol_table.add_column("Mod State", style="blue")
                vol_table.add_column("Mod %", style="bright_blue")
                vol_table.add_column("Can Modify", style="white")
                
                for vol in volumes:
                    # Access SDK model attributes or additional_properties
                    size = vol.size if vol.size is not UNSET else vol.additional_properties.get('Size', 'N/A')
                    vol_type = vol.volume_type if vol.volume_type is not UNSET else vol.additional_properties.get('VolumeType', 'N/A')
                    state = vol.state if vol.state is not UNSET else vol.additional_properties.get('State', 'N/A')
                    mod_state = vol.mod_state if vol.mod_state is not UNSET else vol.additional_properties.get('ModState', 'N/A')
                    mod_progress = vol.mod_progress if vol.mod_progress is not UNSET else vol.additional_properties.get('ModProgress', 'N/A')
                    can_modify = vol.can_modify_now if vol.can_modify_now is not UNSET else vol.additional_properties.get('CanModifyNow', False)
                    mod_last_time = vol.mod_last_time if vol.mod_last_time is not UNSET else vol.additional_properties.get('ModLastTime')
                    
                    # Calculate cooldown info
                    if can_modify:
                        modify_status = "Yes"
                    else:
                        cooldown = calculate_cooldown_info(mod_last_time)
                        if cooldown['in_cooldown']:
                            modify_status = f"In ~{cooldown['wait_str']}"
                        else:
                            modify_status = "No"
                    
                    vol_table.add_row(
                        str(size),
                        str(vol_type),
                        state,
                        mod_state,
                        f"{mod_progress}%" if mod_progress != 'N/A' else 'N/A',
                        modify_status
                    )
                
                console.print(vol_table)
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                console.print(error_msg)
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")
            
    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")

@app.command("create")
def create_zpool(
    ctx: typer.Context,
    size: int = typer.Option(125, help="Size in GiB (must be 125 during beta)"),
    volume_type: str = typer.Option("gp3", help="EBS volume type (gp3, sc1)"),
    watch: bool = typer.Option(False, "--watch", help="Watch creation until it completes"),
    resume: bool = typer.Option(False, "--resume", help="Resume monitoring an existing creation job"),
    timeout: int = typer.Option(1800, "--timeout", help="Timeout in seconds when using --watch or --resume (default: 1800)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Create a new ZPool."""
    try:
        client = get_authenticated_client(ctx.obj)
        
        # If --resume, find existing create job and monitor it
        if resume:
            final_job = find_and_resume_job(
                client,
                job_type='zpool_create',
                operation_name='ZPool creation',
                timeout=timeout,
                json_output=json_output
            )
            # Extract zpool_id from message if available (only in non-JSON mode)
            if not json_output and final_job:
                msg = final_job.get('current_status', {}).get('message', '')
                if 'zpool_id:' in msg:
                    zpool_id = msg.split('zpool_id:')[1].strip()
                    console.print(f"ZPool ID: [cyan]{zpool_id}[/cyan]")
            return
        
        response = client.create_zpool(size_gib=size, volume_type=volume_type)
        
        if response.status_code == 202:
            job_id = response.parsed.detail.job_id
            
            if json_output and not watch:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
            elif not watch:
                console.print(f"[green]ZPool creation started![/green]")
                console.print(f"Job ID: {job_id}")
            
            # Watch for completion if requested
            if watch:
                if json_output:
                    from zpools.helpers import JobPoller
                    poller = JobPoller(client, job_id, timeout=timeout, poll_interval=10)
                    final_job = poller.wait_for_completion()
                    print(json.dumps(final_job, indent=2, default=str))
                else:
                    try:
                        final_job = wait_for_job_with_progress(
                            client, job_id, "ZPool creation", timeout=timeout, poll_interval=5
                        )
                        # Extract zpool_id from message if available
                        msg = final_job.get('current_status', {}).get('message', '')
                        if 'zpool_id:' in msg:
                            zpool_id = msg.split('zpool_id:')[1].strip()
                            console.print(f"ZPool ID: [cyan]{zpool_id}[/cyan]")
                    except TimeoutError:
                        console.print(f"[red]Timeout waiting for job to complete[/red]")
                        console.print(f"Job ID: {job_id}")
                    except RuntimeError:
                        console.print(f"Job ID: {job_id}")
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")

    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")

@app.command("delete")
def delete_zpool(
    ctx: typer.Context,
    zpool_id: str = typer.Argument(..., help="ZPool ID to delete"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Delete a ZPool."""
    if not json_output:
        confirm = typer.confirm(f"Are you sure you want to delete ZPool {zpool_id}?")
        if not confirm:
            return

    try:
        client = get_authenticated_client(ctx.obj)
        auth_client = client.get_authenticated_client()
        
        response = delete_zpool_zpool_id.sync_detailed(zpool_id=zpool_id, client=auth_client)
        
        if response.status_code == 200:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
            else:
                console.print(f"[green]ZPool {zpool_id} deleted successfully.[/green]")
        elif response.status_code == 404:
            if json_output:
                print(json.dumps({"error": "Not found"}, indent=2))
            else:
                console.print(f"[red]ZPool {zpool_id} not found.[/red]")
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(json.dumps({"error": error_msg}, indent=2))
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")

    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")

@app.command("modify")
def modify_zpool(
    ctx: typer.Context,
    zpool_id: str = typer.Argument(..., help="ZPool ID to modify"),
    volume_type: str = typer.Option(None, "--type", help="Target volume type (gp3 or sc1)"),
    watch: bool = typer.Option(False, "--watch", help="Watch modification until it completes after submission"),
    wait_until_able: bool = typer.Option(False, "--wait-until-able", help="Wait until cooldown period expires, then submit modification"),
    resume: bool = typer.Option(False, "--resume", help="Resume monitoring an existing modification in progress"),
    timeout: int = typer.Option(1800, "--timeout", help="Timeout in seconds for modification monitoring (applies to --watch and --resume only)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON response"),
    use_local_tz: bool = typer.Option(False, "--local", help="Show timestamps in local timezone (default: UTC)")
):
    """Change a ZPool's EBS volume type (gp3 <-> sc1).
    
    AWS enforces a 6-hour cooldown between volume modifications. Use --wait-until-able
    to automatically wait for the cooldown to expire before submitting the modification.
    The cooldown wait has no timeout since the end time is known; use Ctrl+C to abort if needed.
    """
    try:
        client = get_authenticated_client(ctx.obj)
        
        # If --resume, skip the API call and just monitor
        if resume:
            if json_output:
                from zpools.helpers import ModifyPoller
                poller = ModifyPoller(client, zpool_id, timeout=timeout, poll_interval=10)
                final_zpool = poller.wait_for_completion()
                print(json.dumps(final_zpool, indent=2, default=str))
            else:
                console.print(f"[cyan]Resuming monitoring of ZPool {zpool_id} modification...[/cyan]")
                try:
                    final_zpool = wait_for_modify_with_progress(
                        client, zpool_id, timeout=timeout, poll_interval=10
                    )
                except TimeoutError:
                    console.print(f"[red]Timeout waiting for modification to complete[/red]")
                except Exception as e:
                    console.print(f"[red]Error waiting for completion: {e}[/red]")
            return
        
        # Normal flow: submit modification
        if not volume_type:
            console.print("[red]Error:[/red] --type is required when not using --resume")
            raise typer.Exit(1)
        
        # If --wait-until-able, check for cooldown and wait if needed
        if wait_until_able:
            list_response = get_zpools.sync_detailed(client=client.get_authenticated_client())
            if list_response.status_code == 200 and list_response.parsed:
                zpools = list_response.parsed.detail.zpools.to_dict() if list_response.parsed.detail.zpools else {}
                zpool = zpools.get(zpool_id, {})
                volumes = zpool.get('Volumes', [])
                
                # Find the latest ModLastTime among volumes that can't be modified
                max_cooldown = None
                for vol in volumes:
                    if not vol.get('CanModifyNow', True):
                        mod_last = vol.get('ModLastTime')
                        cooldown = calculate_cooldown_info(mod_last)
                        if cooldown['in_cooldown']:
                            if max_cooldown is None or cooldown['wait_seconds'] > max_cooldown['wait_seconds']:
                                max_cooldown = cooldown
                
                if max_cooldown:
                    retry_time = max_cooldown['retry_time']
                    retry_time_str = format_timestamp(retry_time, use_local_tz)
                    
                    # Create table for cooldown wait status
                    cooldown_table = Table(show_header=False, box=None, padding=(0, 2))
                    cooldown_table.add_column(style="yellow", width=20)
                    cooldown_table.add_column(style="white")
                    cooldown_table.add_row("[yellow]Status:[/yellow]", "[yellow]Volume is in cooldown period[/yellow]")
                    cooldown_table.add_row("[yellow]Waiting until:[/yellow]", f"[white]{retry_time_str}[/white]")
                    console.print(cooldown_table)
                    
                    # Wait with periodic token refresh (shows progress if interactive terminal)
                    wait_with_token_refresh(client, max_cooldown['wait_seconds'], console=console, use_local_tz=use_local_tz)
                    
                    # After long wait, ensure we have a fresh token for the modify call
                    try:
                        client.get_authenticated_client()
                    except Exception:
                        # Token refresh failed - recreate client to force re-authentication
                        client = get_authenticated_client(ctx.obj)
                    
                    console.print()
                    console.print("[green]✓ Cooldown period expired. Submitting modification...[/green]")
                    console.print()
        
        response = client.modify_zpool(zpool_id, target_volume_type=volume_type)
        
        if response.status_code == 202:
            if json_output and not watch:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
            elif not watch:
                console.print(f"[green]ZPool {zpool_id} volume type modification submitted.[/green]")
                if response.parsed and response.parsed.detail:
                    summary = response.parsed.detail.summary
                    console.print(f"Submitted: {summary.submitted}/{summary.discovered} volumes")
            
            # Watch for completion if requested
            if watch:
                if json_output:
                    from zpools.helpers import ModifyPoller
                    poller = ModifyPoller(client, zpool_id, timeout=timeout, poll_interval=10)
                    final_zpool = poller.wait_for_completion()
                    print(json.dumps(final_zpool, indent=2, default=str))
                else:
                    try:
                        final_zpool = wait_for_modify_with_progress(
                            client, zpool_id, timeout=timeout, poll_interval=10
                        )
                    except TimeoutError:
                        console.print(f"[red]Timeout waiting for modification to complete[/red]")
                    except Exception as e:
                        console.print(f"[red]Error waiting for completion: {e}[/red]")
        elif response.status_code == 409:
            # Parse the 409 response to provide helpful wait time information
            try:
                # Parse the JSON response directly since the SDK doesn't parse 409 responses
                conflict_data = json.loads(response.content)
                message = conflict_data.get('message', 'Conflict occurred')
                detail = conflict_data.get('detail', {})
                ineligible = detail.get('ineligible', [])
                
                # Check if volumes are in cooldown
                cooldown_volumes = [v for v in ineligible if v.get('reason') == 'cooldown_or_active_modify']
                
                if cooldown_volumes:
                    # Get volume details from list to find ModLastTime
                    list_response = get_zpools.sync_detailed(client=client.get_authenticated_client())
                    if list_response.status_code == 200 and list_response.parsed:
                        zpools = list_response.parsed.detail.zpools.to_dict() if list_response.parsed.detail.zpools else {}
                        zpool = zpools.get(zpool_id, {})
                        volumes = zpool.get('Volumes', [])
                        
                        # Find the earliest cooldown expiration time
                        earliest_cooldown = None
                        
                        # In MVP: one volume per zpool, so if any cooldown volume matches this zpool, show it
                        if cooldown_volumes:
                            for vol in volumes:
                                mod_last = vol.get('ModLastTime')
                                cooldown = calculate_cooldown_info(mod_last)
                                if cooldown['in_cooldown']:
                                    if earliest_cooldown is None or cooldown['retry_time'] < earliest_cooldown['retry_time']:
                                        earliest_cooldown = cooldown
                        
                        if earliest_cooldown:
                            retry_time_str = format_timestamp(earliest_cooldown['retry_time'], use_local_tz)
                            console.print(f"[yellow]Conflict:[/yellow] {message}")
                            console.print(f"[yellow]AWS requires a 6-hour cooldown between volume modifications.[/yellow]")
                            console.print(f"[yellow]You can retry after: {retry_time_str} (in ~{earliest_cooldown['wait_str']})[/yellow]")
                        else:
                            console.print(f"[yellow]Conflict:[/yellow] {message}")
                    else:
                        console.print(f"[yellow]Conflict:[/yellow] {message}")
                else:
                    console.print(f"[yellow]Conflict:[/yellow] {message}")
            except Exception as e:
                # Fallback to simple message if parsing fails
                error_msg = format_error_response(response.status_code, response.content, json_output)
                console.print(f"[yellow]Conflict:[/yellow] {error_msg}")
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(json.dumps({"error": error_msg}, indent=2))
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")

    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")

@app.command("expand")
def expand_zpool(
    ctx: typer.Context,
    zpool_id: str = typer.Argument(..., help="ZPool ID to expand"),
    size: int = typer.Option(..., "--size", help="New size in GiB"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Expand a ZPool's size (Not Yet Implemented)."""
    console.print("[yellow]ZPool expansion is not yet implemented.[/yellow]")
    console.print("This feature is planned for a future release.")
    console.print("\nExpansion will:")
    console.print("  • Resize EBS volumes")
    console.print("  • Expand ZFS pool to use new space")
    console.print("  • Track progress via async job")
    raise typer.Exit(1)

@app.command("scrub")
def scrub_zpool(
    ctx: typer.Context,
    zpool_id: str = typer.Argument(..., help="ZPool ID to scrub"),
    watch: bool = typer.Option(False, "--watch", help="Watch scrub until it completes"),
    resume: bool = typer.Option(False, "--resume", help="Resume monitoring an existing scrub"),
    timeout: int = typer.Option(1800, "--timeout", help="Timeout in seconds when using --watch or --resume (default: 1800)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Start a scrub on a ZPool."""
    try:
        client = get_authenticated_client(ctx.obj)
        
        # If --resume, find existing scrub job and monitor it
        if resume:
            find_and_resume_job(
                client,
                job_type='zpool_scrub',
                operation_name='ZPool scrub',
                zpool_id=zpool_id,
                timeout=timeout,
                json_output=json_output
            )
            return
        
        # Normal flow: start a new scrub
        response = client.scrub_zpool(zpool_id)
        
        if response.status_code == 202:
            job_id = response.parsed.detail.job_id
            
            if json_output and not watch:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
            elif not watch:
                console.print(f"[green]Scrub started for ZPool {zpool_id}.[/green]")
                console.print(f"Job ID: {job_id}")
            
            # Watch for completion if requested
            if watch:
                if json_output:
                    from zpools.helpers import JobPoller
                    poller = JobPoller(client, job_id, timeout=timeout, poll_interval=5)
                    final_job = poller.wait_for_completion()
                    print(json.dumps(final_job, indent=2, default=str))
                else:
                    try:
                        final_job = wait_for_job_with_progress(
                            client, job_id, "ZPool scrub", timeout=timeout, poll_interval=5
                        )
                    except TimeoutError:
                        console.print(f"[red]Timeout waiting for scrub to complete[/red]")
                        console.print(f"Job ID: {job_id}")
                    except RuntimeError:
                        console.print(f"Job ID: {job_id}")
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(error_msg)
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")

    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")
