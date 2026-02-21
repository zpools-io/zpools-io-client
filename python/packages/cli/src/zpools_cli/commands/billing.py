import typer
import json
from rich.console import Console
from rich.table import Table
from zpools_cli.utils import format_error_response, format_usd, format_timestamp
from zpools._generated.api.billing import (
    get_billing_balance,
    get_billing_ledger,
    get_billing_runway,
    get_billing_summary,
)
from zpools._generated.types import UNSET
from zpools_cli.help_scopes import ScopedGroup
import datetime

app = typer.Typer(help="Manage billing and payments", no_args_is_help=True, cls=ScopedGroup)
console = Console()

@app.command("balance")
def get_balance(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON")
):
    """Get current account balance."""
    try:
        from zpools_cli.utils import get_authenticated_client
        client = get_authenticated_client(ctx.obj)
        auth_client = client.get_authenticated_client()
        
        response = get_billing_balance.sync_detailed(client=auth_client)
        
        if response.status_code == 200:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
                return
            
            balance_obj = response.parsed.detail.balance
            # Check if balance_obj is Unset or None
            if not balance_obj or isinstance(balance_obj, type(UNSET)):
                 console.print("[yellow]Balance information unavailable.[/yellow]")
                 return
            
            # Access balance_usd from the object
            balance_usd = balance_obj.balance_usd if balance_obj.balance_usd is not UNSET else 0
            console.print(f"[bold]Current Balance:[/bold] ${format_usd(balance_usd)}")
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(error_msg)
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")
            
    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")

@app.command("ledger")
def get_ledger(
    ctx: typer.Context,
    limit: int = typer.Option(None, help="Number of entries to display"),
    since: str = typer.Option(None, help="Start event date (YYYY-MM-DD) - filters by when event occurred"),
    until: str = typer.Option(None, help="End event date (YYYY-MM-DD) - filters by when event occurred"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    use_local_tz: bool = typer.Option(False, "--local", help="Show timestamps in local timezone (default: UTC)")
):
    """View billing transaction history. Shows event_ts (when event occurred) and posted_ts (when recorded)."""
    try:
        from zpools_cli.utils import get_authenticated_client
        client = get_authenticated_client(ctx.obj)
        auth_client = client.get_authenticated_client()
        
        # Parse dates if provided
        since_date = None
        if since:
            try:
                since_date = datetime.datetime.strptime(since, "%Y-%m-%d").date()
            except ValueError:
                console.print("[red]Invalid date format for --since. Use YYYY-MM-DD[/red]")
                return

        until_date = None
        if until:
            try:
                until_date = datetime.datetime.strptime(until, "%Y-%m-%d").date()
            except ValueError:
                console.print("[red]Invalid date format for --until. Use YYYY-MM-DD[/red]")
                return

        today = datetime.date.today()
        if since_date is not None and since_date > today:
            console.print("[red]--since must not be a future date.[/red]")
            return
        if until_date is not None and until_date > today:
            console.print("[red]--until must not be a future date.[/red]")
            return

        # Build kwargs for API call (API returns newest-first)
        kwargs = {}
        if limit:
            kwargs["limit"] = limit
        if since_date:
            kwargs["since"] = since_date
        if until_date:
            kwargs["until"] = until_date

        response = get_billing_ledger.sync_detailed(client=auth_client, **kwargs)
        
        if response.status_code == 200:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
                return
            
            items = response.parsed.detail.items
            if not items or items is UNSET:
                console.print("No transactions found.")
                return

            table = Table(title="Billing Ledger")
            table.add_column("Event", style="green")
            table.add_column("Posted", style="blue")
            table.add_column("Event Type", style="yellow")
            table.add_column("Source", style="cyan")
            table.add_column("Amount (USD)", style="magenta")
            table.add_column("Note", style="white")

            # API returns newest-first, display as-is
            for item in items:
                # Extract fields with UNSET checks
                event_ts = item.event_ts if item.event_ts is not UNSET else ""
                posted_ts = item.posted_ts if item.posted_ts is not UNSET else ""
                event_type = item.event_type if item.event_type is not UNSET else ""
                source = item.source if item.source is not UNSET else ""
                amount_usd = item.amount_usd if item.amount_usd is not UNSET else 0
                note = item.note if item.note is not UNSET else ""
                
                # Format timestamps with timezone preference
                event_ts_fmt = format_timestamp(event_ts, use_local_tz)
                posted_ts_fmt = format_timestamp(posted_ts, use_local_tz)
                
                # Format amount with color
                amount_str = f"${format_usd(amount_usd)}"
                if amount_usd > 0:
                    amount_str = f"[green]+{amount_str}[/green]"
                elif amount_usd < 0:
                    amount_str = f"[red]{amount_str}[/red]"
                
                table.add_row(
                    event_ts_fmt,
                    posted_ts_fmt,
                    event_type,
                    source,
                    amount_str,
                    note
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


@app.command("summary")
def get_summary(
    ctx: typer.Context,
    since: str = typer.Option(None, help="Start date (YYYY-MM-DD)"),
    until: str = typer.Option(None, help="End date (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
    use_local_tz: bool = typer.Option(False, "--local", help="Show timestamps in local timezone (default: UTC)")
):
    """View aggregated billing summary grouped by zpool and rate period."""
    try:
        from zpools_cli.utils import get_authenticated_client
        client = get_authenticated_client(ctx.obj)
        auth_client = client.get_authenticated_client()

        # Parse dates if provided
        since_date = None
        if since:
            try:
                since_date = datetime.datetime.strptime(since, "%Y-%m-%d").date()
            except ValueError:
                console.print("[red]Invalid date format for --since. Use YYYY-MM-DD[/red]")
                return

        until_date = None
        if until:
            try:
                until_date = datetime.datetime.strptime(until, "%Y-%m-%d").date()
            except ValueError:
                console.print("[red]Invalid date format for --until. Use YYYY-MM-DD[/red]")
                return

        today = datetime.date.today()
        if since_date is not None and since_date > today:
            console.print("[red]--since must not be a future date.[/red]")
            return
        if until_date is not None and until_date > today:
            console.print("[red]--until must not be a future date.[/red]")
            return

        # Build kwargs for API call
        kwargs = {}
        if since_date:
            kwargs["since"] = since_date
        if until_date:
            kwargs["until"] = until_date

        response = get_billing_summary.sync_detailed(client=auth_client, **kwargs)

        if response.status_code == 200:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
                return

            summary = response.parsed.detail.summary
            if not summary or isinstance(summary, type(UNSET)):
                console.print("[yellow]Summary information unavailable.[/yellow]")
                return

            # Period info
            period = summary.period if summary.period is not UNSET else None
            if period:
                from_date = period.from_date if period.from_date is not UNSET else "all time"
                to_date = period.to_date if period.to_date is not UNSET else "present"
                console.print(f"\n[bold]Billing Summary[/bold] ({from_date} to {to_date})\n")

            # Storage Charges
            storage_charges = summary.storage_charges if summary.storage_charges is not UNSET else []
            if storage_charges:
                table = Table(title="Storage Charges")
                table.add_column("Zpool ID", style="cyan")
                table.add_column("Type", style="yellow")
                table.add_column("Size", style="green")
                table.add_column("Hourly Rate", style="blue")
                table.add_column("Daily Rate", style="blue")
                table.add_column("Hours", style="magenta")
                table.add_column("Total", style="red")
                table.add_column("Period", style="white")

                for charge in storage_charges:
                    zpool_id = charge.zpool_id if charge.zpool_id is not UNSET else ""
                    vol_type = charge.volume_type if charge.volume_type is not UNSET else ""
                    size_gb = charge.size_gb if charge.size_gb is not UNSET else 0
                    hourly = charge.hourly_rate if charge.hourly_rate is not UNSET else 0
                    daily = charge.daily_rate if charge.daily_rate is not UNSET else 0
                    hours = charge.hours if charge.hours is not UNSET else 0
                    total = charge.total_charges if charge.total_charges is not UNSET else 0
                    from_ts = charge.from_ts if charge.from_ts is not UNSET else ""
                    to_ts = charge.to_ts if charge.to_ts is not UNSET else ""

                    # Format dates for display (just date part)
                    from_short = from_ts[:10] if from_ts else ""
                    to_short = to_ts[:10] if to_ts else ""
                    period_str = f"{from_short} → {to_short}"

                    table.add_row(
                        zpool_id,
                        vol_type,
                        f"{size_gb} GB",
                        f"${format_usd(hourly)}",
                        f"${format_usd(daily)}",
                        str(hours),
                        f"${format_usd(total)}",
                        period_str
                    )
                console.print(table)

            # Time-of-Use summary (aggregated; use billing ledger for per-entry detail)
            tou_summary = summary.time_of_use_summary if summary.time_of_use_summary is not UNSET else None
            if tou_summary and tou_summary.by_source is not UNSET:
                by_src = tou_summary.by_source
                zero_egress = tou_summary.zero_egress_count if tou_summary.zero_egress_count is not UNSET else 0
                keys = sorted(by_src.additional_properties.keys()) if by_src.additional_properties else []
                if keys:
                    table = Table(title="Time-of-Use (summary)")
                    table.add_column("Source", style="cyan")
                    table.add_column("Count", style="blue")
                    table.add_column("Total (USD)", style="red")
                    table.add_column("Zero count", style="dim")
                    for src in keys:
                        data = by_src[src]
                        count = data.count if data.count is not UNSET else 0
                        total_usd = data.total_usd if data.total_usd is not UNSET else 0
                        zc = data.zero_count if data.zero_count is not UNSET else 0
                        table.add_row(src, str(count), f"${format_usd(total_usd)}", str(zc))
                    console.print(table)
                    if zero_egress:
                        console.print(f"  [dim]Zero-egress entries: {zero_egress}[/dim]")

            # Credits (attribute is credits_ due to Python reserved word)
            credits_list = summary.credits_ if summary.credits_ is not UNSET else []
            if credits_list:
                table = Table(title="Credits")
                table.add_column("Time", style="blue")
                table.add_column("Source", style="cyan")
                table.add_column("Amount", style="green")
                table.add_column("Note", style="white")

                for credit in credits_list:
                    posted_ts = credit.posted_ts if credit.posted_ts is not UNSET else ""
                    source = credit.source if credit.source is not UNSET else ""
                    amount = credit.amount_usd if credit.amount_usd is not UNSET else 0
                    note = credit.note if credit.note is not UNSET else ""

                    table.add_row(format_timestamp(posted_ts, use_local_tz), source, f"+${format_usd(amount)}", note)
                console.print(table)

            # Totals
            totals = summary.totals if summary.totals is not UNSET else None
            if totals:
                storage = totals.storage_charges if totals.storage_charges is not UNSET else 0
                tou = totals.time_of_use_charges if totals.time_of_use_charges is not UNSET else 0
                credits_applied = totals.credits_applied if totals.credits_applied is not UNSET else 0
                period_net = totals.period_net if totals.period_net is not UNSET else 0
                ending_balance = totals.ending_balance if totals.ending_balance is not UNSET else 0

                # Period-specific totals
                console.print(f"\n[bold]Period Totals[/bold] [dim]({from_date} to {to_date})[/dim]")
                console.print(f"  Storage Charges:     [red]-${format_usd(storage)}[/red]")
                console.print(f"  Time-of-Use Charges: [red]-${format_usd(tou)}[/red]")
                console.print(f"  Credits Applied:     [green]+${format_usd(credits_applied)}[/green]")
                console.print(f"  [bold]Net Change:          ${format_usd(period_net)}[/bold]")

                # Current account balance (independent of period)
                console.print(f"\n[bold]Account Balance[/bold]")
                console.print(f"  [bold]Balance Now:         ${format_usd(ending_balance)}[/bold]")

            # Note about ending balance
            note = response.parsed.detail.note if response.parsed.detail.note is not UNSET else ""
            if note:
                console.print(f"\n[dim]{note}[/dim]")
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(error_msg)
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")

    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")


@app.command("runway")
def get_runway(
    ctx: typer.Context,
    lookback_days: int = typer.Option(30, "--lookback", "--lookback-days", help="Days of ToU history for adjusted runway (1–90)"),
    json_output: bool = typer.Option(False, "--json", help="Output raw JSON"),
):
    """Show burn rate and days remaining (EBS-only and time-of-use adjusted)."""
    try:
        from zpools_cli.utils import get_authenticated_client
        client = get_authenticated_client(ctx.obj)
        auth_client = client.get_authenticated_client()

        if lookback_days < 1 or lookback_days > 90:
            console.print("[red]--lookback-days must be between 1 and 90.[/red]")
            return

        response = get_billing_runway.sync_detailed(client=auth_client, lookback_days=lookback_days)

        if response.status_code == 200:
            if json_output:
                print(json.dumps(response.parsed.to_dict(), indent=2, default=str))
                return

            runway = response.parsed.detail.runway if response.parsed.detail.runway is not UNSET else None
            if not runway:
                console.print("[yellow]Runway data unavailable.[/yellow]")
                return

            balance = runway.ending_balance if runway.ending_balance is not UNSET else None
            console.print(f"\n[bold]Current balance[/bold]  ${format_usd(balance) if balance is not None else '-'}\n")

            days_ebs = runway.days_remaining_ebs if runway.days_remaining_ebs is not UNSET else None
            burn_ebs = runway.daily_burn_ebs if runway.daily_burn_ebs is not UNSET else None
            if days_ebs is not None and burn_ebs is not None:
                console.print("[bold]EBS-only runway[/bold]  (current storage allocation)")
                console.print(f"  ~{float(days_ebs):.1f} days  (daily burn: ${format_usd(burn_ebs)})")
            else:
                console.print("[bold]EBS-only runway[/bold]  — (no active storage allocation)")

            lookback = runway.lookback_days if runway.lookback_days is not UNSET else lookback_days
            days_adj = runway.days_remaining_adjusted if runway.days_remaining_adjusted is not UNSET else None
            burn_tou = runway.daily_tou_avg if runway.daily_tou_avg is not UNSET else None
            burn_total = runway.daily_burn_total if runway.daily_burn_total is not UNSET else None
            if days_adj is not None and burn_total is not None:
                console.print(f"\n[bold]Runway (incl. time-of-use)[/bold]  (last {lookback} days)")
                console.print(f"  ~{float(days_adj):.1f} days  (combined daily burn: ${format_usd(burn_total)})")
                if burn_tou is not None:
                    console.print(f"  [dim]ToU avg: ${format_usd(burn_tou)}/day[/dim]")
            else:
                tou_total = runway.tou_total_in_lookback if runway.tou_total_in_lookback is not UNSET else None
                console.print(f"\n[bold]Runway (incl. time-of-use)[/bold]  — (ToU in period: ${format_usd(tou_total) if tou_total is not None else '-'})")
        else:
            error_msg = format_error_response(response.status_code, response.content, json_output)
            if json_output:
                print(error_msg)
            else:
                console.print(f"[red]Error {response.status_code}:[/red] {error_msg}")

    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")
