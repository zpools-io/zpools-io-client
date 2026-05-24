from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import Group
from zpools_cli.progress import ProgressMonitor


def wait_for_modify_with_progress(client, zpool_id: str, timeout: int = 43200, poll_interval: int = 60) -> dict:
    """
    Wait for zpool volume modifications to complete with live progress display.
    
    Polls the zpool list endpoint to check volume modification states.
    
    Args:
        client: ZPoolsClient instance
        zpool_id: ZPool ID to monitor
        timeout: Maximum time to wait in seconds
        poll_interval: Time between polls in seconds
        
    Returns:
        Final zpool data dict
        
    Raises:
        TimeoutError: If modifications don't complete within timeout
        RuntimeError: If zpool disappears or API errors
    """
    console = Console()
    monitor = ProgressMonitor(console, poll_interval=poll_interval, timeout=timeout)
    
    def poll_api():
        """Poll zpool status."""
        response = client.list_zpools()
        if response.status_code != 200:
            raise RuntimeError(f"Failed to list zpools: {response.status_code}")
        
        zpools = response.parsed.detail.zpools.to_dict() if response.parsed.detail.zpools else {}
        zpool = zpools.get(zpool_id)
        
        if not zpool:
            raise RuntimeError(f"Zpool {zpool_id} not found in list")
        
        volumes = zpool.get('Volumes', zpool.get('volumes', []))
        return {'zpool': zpool, 'volumes': volumes}
    
    def render_display(state, spinner):
        """Render the modification progress display."""
        volumes = state['volumes']
        
        # Status line
        status_text = Text()
        status_text.append(f"{spinner} ", style="cyan bold")
        status_text.append(f"Modifying volumes for ZPool {zpool_id}", style="white")
        status_text.append(f" ({monitor.elapsed_str()})", style="dim")
        
        # Build volume status table
        vol_table = Table(show_header=True, box=None, padding=(0, 1))
        vol_table.add_column("Volume", style="dim", width=22)
        vol_table.add_column("State", style="cyan", width=12)
        vol_table.add_column("Mod State", style="yellow", width=12)
        vol_table.add_column("Progress", style="green", width=10)
        vol_table.add_column("Type", style="magenta", width=8)
        
        for vol in volumes:
            vol_id = vol.get('VolumeId', vol.get('volume_id', 'N/A'))
            vol_state = vol.get('State', vol.get('state', 'N/A'))
            mod_state = vol.get('ModState', vol.get('mod_state', 'none'))
            mod_progress = vol.get('ModProgress', vol.get('mod_progress', 0))
            vol_type = vol.get('VolumeType', vol.get('volume_type', 'N/A'))
            
            # Format progress
            if mod_state in ('modifying', 'optimizing'):
                progress_str = f"{mod_progress}%"
            elif mod_state == 'completed':
                progress_str = "✓ Done"
            else:
                progress_str = "-"
            
            vol_table.add_row(vol_id[-12:], vol_state, mod_state, progress_str, vol_type)
        
        # Combine into panel
        content = Group(
            status_text,
            vol_table if volumes else Text("No volume info available", style="dim")
        )
        return Panel(
            content,
            title=f"[bold]ZPool {zpool_id} - Volume Modifications[/bold]",
            border_style="blue"
        )
    
    def check_complete(state):
        """Check if all modifications are complete."""
        volumes = state['volumes']
        
        # Check if any volumes are actively modifying
        any_modifying = False
        all_complete = True
        
        for vol in volumes:
            mod_state = vol.get('ModState', vol.get('mod_state', 'none'))
            if mod_state in ('modifying', 'optimizing'):
                any_modifying = True
                all_complete = False
                break
            elif mod_state == 'completed':
                # At least one was modified
                pass
        
        if not any_modifying:
            # Check if there were any recent modifications (completed state)
            has_completed = any(
                vol.get('ModState', vol.get('mod_state', 'none')) == 'completed'
                for vol in volumes
            )
            
            if has_completed or all_complete:
                console.print(f"\n[green]✓ Volume modifications completed successfully![/green]")
            else:
                console.print(f"\n[yellow]No active modifications found for ZPool {zpool_id}[/yellow]")
            return True
        
        return False
    
    result = monitor.monitor(poll_api, render_display, check_complete, "Modify operation")
    return result['zpool']
