"""Configuration loading for zpools CLI."""
import getpass
import os
import sys
import webbrowser
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlencode, urlparse, urlunparse

from rich.box import ROUNDED
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

try:
    import termios
    import tty
    _HAS_TERMIOS = True
except ImportError:
    _HAS_TERMIOS = False

DEFAULT_SSH_KEY_PATH = "~/.ssh/id_zpool_ed25519"
DEFAULT_SSH_KEYGEN_CMD = f"ssh-keygen -t ed25519 -f {DEFAULT_SSH_KEY_PATH}"

# Commands that require a config file (and will trigger the wizard if none exists)
COMMANDS_NEEDING_CONFIG = ("hello", "zpool", "sshkey", "pat", "job", "billing", "zfs")

# PAT scopes for the configure wizard (id, short description). Order matches dashboard tokens page.
PAT_SCOPES = [
    ("sshkey", "Manage SSH keys (list, add, delete)"),
    ("job", "List and inspect jobs"),
    ("zpool", "Create and manage zpools"),
    ("pat", "List and revoke PATs via API"),
    ("billing", "Billing (read); usually not needed for CLI"),
    ("*", "All PAT-enabled endpoints (wildcard)"),
]


def _is_valid_api_url(s: str) -> bool:
    """True if s looks like an API URL (scheme, host with no spaces)."""
    if not s or not s.strip():
        return False
    parsed = urlparse(s.strip())
    if not parsed.scheme or not parsed.netloc:
        return False
    host = parsed.netloc.split(":")[0]
    if " " in host or "\n" in host or "[" in host:
        return False
    return True


def api_url_to_website_base_url(api_url: str) -> str:
    """
    Derive website base URL from API URL.
    e.g. https://api.zpools.io/v1 -> https://zpools.io
         https://api.dev.zpools.io/v1 -> https://dev.zpools.io
    """
    if not _is_valid_api_url(api_url):
        return "https://zpools.io"
    parsed = urlparse(api_url)
    if not parsed.scheme or not parsed.netloc:
        return "https://zpools.io"
    host = parsed.netloc.split(":")[0]
    if host.startswith("api."):
        base_host = host[4:]  # strip "api."
        return urlunparse((parsed.scheme or "https", base_host, "", "", "", ""))
    return urlunparse((parsed.scheme or "https", host, "", "", "", ""))


def _build_tokens_url(
    api_url: str,
    label: Optional[str] = None,
    scopes: Optional[str] = None,
    expiry: Optional[str] = None,
) -> str:
    """Build dashboard tokens page URL with optional query params (create=1, label, scopes, expiry)."""
    base = api_url_to_website_base_url(api_url)
    url = f"{base.rstrip('/')}/dashboard/tokens"
    params: Dict[str, str] = {}
    params["create"] = "1"
    if label and label.strip():
        params["label"] = label.strip()
    if scopes and scopes.strip():
        params["scopes"] = scopes.strip().replace(" ", "")
    if expiry and expiry.strip():
        params["expiry"] = expiry.strip()
    if params:
        url = f"{url}?{urlencode(params)}"
    return url


def _read_key() -> Optional[str]:
    """Read one key from stdin (up, down, space, enter). Returns None if not a TTY or on error."""
    if not _HAS_TERMIOS or not sys.stdin.isatty():
        return None
    fd = sys.stdin.fileno()
    try:
        old = termios.tcgetattr(fd)
    except termios.error:
        return None
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            sub = sys.stdin.read(2)
            if sub == "[A":
                return "up"
            if sub == "[B":
                return "down"
            return None
        if ch == " ":
            return "space"
        if ch in "\r\n":
            return "enter"
        return None
    except (OSError, KeyboardInterrupt):
        return None
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except termios.error:
            pass


def _prompt_scopes_interactive(console) -> str:
    """
    Interactive scope selection: up/down move, space toggles (or confirms on Accept).
    * is exclusive with other scopes. Accept is dim until at least one scope is selected.
    Returns comma-joined scope ids or '*'.
    """
    if not _HAS_TERMIOS or not sys.stdin.isatty():
        return "zpool,job"
    n_scopes = len(PAT_SCOPES)
    WILDCARD_INDEX = n_scopes - 1  # * is last scope
    cursor = 0  # 0 .. n_scopes (n_scopes = Accept row)
    selected: Set[int] = set()
    ACCEPT_INDEX = n_scopes

    def build_table() -> Table:
        table = Table(box=ROUNDED, show_header=True, header_style="bold")
        table.add_column("", width=1)   # cursor
        table.add_column("", width=1)   # selected (* or space)
        table.add_column("Scope", width=10)
        table.add_column("Description", width=52)
        for i, (scope_id, desc) in enumerate(PAT_SCOPES):
            cur = ">" if cursor == i else " "
            mark = "*" if i in selected else " "
            is_highlight = i in selected
            row_style = "" if is_highlight else "dim"
            table.add_row(cur, mark, scope_id, desc, style=row_style)
        # Accept row: Scope = "Accept"; Description = "choose at least one scope" when dim, else empty
        cur_accept = ">" if cursor == ACCEPT_INDEX else " "
        accept_ready = len(selected) > 0
        accept_style = "" if accept_ready else "dim"
        accept_desc = "" if accept_ready else "choose at least one scope"
        table.add_row(cur_accept, " ", "Accept", accept_desc, style=accept_style)
        return table

    def build_renderable():
        table = build_table()
        footer = "[dim]↑/↓ move   Space toggle or confirm on Accept[/dim]"
        return Panel(Group(table, "", footer), title="PAT scopes", box=ROUNDED, border_style="blue")

    with Live(build_renderable(), console=console, refresh_per_second=4) as live:
        while True:
            live.update(build_renderable())
            key = _read_key()
            if key == "up":
                cursor = max(0, cursor - 1)
            elif key == "down":
                cursor = min(ACCEPT_INDEX, cursor + 1)
            elif key == "space":
                if cursor < n_scopes:
                    if cursor in selected:
                        selected.discard(cursor)
                    else:
                        if cursor == WILDCARD_INDEX:
                            selected.clear()
                            selected.add(WILDCARD_INDEX)
                        else:
                            selected.discard(WILDCARD_INDEX)
                            selected.add(cursor)
                elif cursor == ACCEPT_INDEX and selected:
                    break
            elif key == "enter":
                if cursor == ACCEPT_INDEX and selected:
                    break

    # Build result: if only * is selected, return "*"; else comma-joined ids
    if selected == {WILDCARD_INDEX}:
        return "*"
    return ",".join(PAT_SCOPES[i][0] for i in sorted(selected))


def _prompt_scopes_plaintext(console) -> str:
    """Plaintext scope selection: numbered list, comma-separated numbers. * (6) exclusive; at least one required."""
    n_scopes = len(PAT_SCOPES)
    WILDCARD_INDEX = n_scopes - 1
    for i, (scope_id, desc) in enumerate(PAT_SCOPES):
        print(f"  {i + 1}. {scope_id:<8}  {desc}")
    print("  7. Accept  choose at least one scope")
    while True:
        sys.stdout.write("Enter scope numbers (e.g. 1,2,3). * is 6, exclusive. At least one: ")
        sys.stdout.flush()
        raw = input().strip()
        parts = [p.strip() for p in raw.replace(",", " ").split() if p.strip()]
        indices: Set[int] = set()
        for p in parts:
            try:
                n = int(p)
                if 1 <= n <= 6:
                    indices.add(n - 1)
            except ValueError:
                pass
        if not indices:
            print("Choose at least one scope.")
            continue
        if WILDCARD_INDEX in indices:
            indices = {WILDCARD_INDEX}
        if indices == {WILDCARD_INDEX}:
            return "*"
        return ",".join(PAT_SCOPES[i][0] for i in sorted(indices))


def _parse_iso8601_date(s: str) -> Optional[date]:
    """Parse ISO 8601 date (YYYY-MM-DD). Returns None if invalid."""
    s = s.strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _prompt_expiry_interactive(console) -> str:
    """
    Up/down selector for PAT expiry: presets (1/3/6/12 months from today, max 1 year)
    plus Custom to enter an ISO 8601 date (YYYY-MM-DD). Enter to select.
    """
    today = date.today()
    max_date = today + timedelta(days=365)
    presets: List[Tuple[str, date]] = [
        ("1 month", today + timedelta(days=30)),
        ("3 months", today + timedelta(days=90)),
        ("6 months", today + timedelta(days=180)),
        ("1 year", min(today + timedelta(days=365), max_date)),
    ]
    # Cap preset dates at max_date
    presets = [(label, min(d, max_date)) for label, d in presets]
    options: List[Tuple[str, str]] = [(label, d.isoformat()) for label, d in presets]
    options.append(("Custom (enter YYYY-MM-DD)", ""))

    if not _HAS_TERMIOS or not sys.stdin.isatty():
        return presets[0][1].isoformat()

    cursor = 0
    n = len(options)

    def build_table() -> Table:
        table = Table(box=ROUNDED, show_header=True, header_style="bold")
        table.add_column("", width=1)
        table.add_column("Expiry", width=28)
        table.add_column("Date", width=12)
        for i, (label, iso) in enumerate(options):
            cur = ">" if cursor == i else " "
            date_str = iso if iso else "(enter when selected)"
            table.add_row(cur, label, date_str)
        return table

    def build_renderable():
        return Panel(
            Group(build_table(), "", "[dim]↑/↓ move   Space or Enter to select   Max 1 year from today[/dim]"),
            title="PAT expiry",
            box=ROUNDED,
            border_style="blue",
        )

    with Live(build_renderable(), console=console, refresh_per_second=4) as live:
        while True:
            live.update(build_renderable())
            key = _read_key()
            if key == "up":
                cursor = max(0, cursor - 1)
            elif key == "down":
                cursor = min(n - 1, cursor + 1)
            elif key in ("enter", "space"):
                if cursor < n - 1:
                    return options[cursor][1]
                break

    # Custom selected: prompt for ISO 8601 date
    while True:
        sys.stdout.write("Expiry date (YYYY-MM-DD, max 1 year from today): ")
        sys.stdout.flush()
        raw = input().strip()
        if not raw:
            return presets[0][1].isoformat()
        d = _parse_iso8601_date(raw)
        if d is None:
            console.print("[red]Invalid date. Use ISO 8601 (YYYY-MM-DD).[/red]")
            continue
        if d < today:
            console.print("[red]Expiry must be today or in the future.[/red]")
            continue
        if d > max_date:
            console.print("[red]Expiry must be at most 1 year from today.[/red]")
            continue
        return d.isoformat()


def _prompt_expiry_plaintext(console) -> str:
    """Plaintext expiry: numbered presets 1-4, 5 = custom (ISO 8601 date, max 1 year)."""
    today = date.today()
    max_date = today + timedelta(days=365)
    presets: List[Tuple[str, date]] = [
        ("1 month", today + timedelta(days=30)),
        ("3 months", today + timedelta(days=90)),
        ("6 months", today + timedelta(days=180)),
        ("1 year", min(today + timedelta(days=365), max_date)),
    ]
    presets = [(label, min(d, max_date)) for label, d in presets]
    for i, (label, d) in enumerate(presets, 1):
        print(f"  {i}. {label:<12}  {d.isoformat()}")
    print("  5. Custom (YYYY-MM-DD)")
    while True:
        sys.stdout.write("Enter number (1-5): ")
        sys.stdout.flush()
        raw = input().strip()
        if raw == "5":
            break
        if raw in ("1", "2", "3", "4"):
            return presets[int(raw) - 1][1].isoformat()
        print("Enter 1, 2, 3, 4, or 5.")
    while True:
        sys.stdout.write("Expiry date (YYYY-MM-DD, max 1 year from today): ")
        sys.stdout.flush()
        raw = input().strip()
        if not raw:
            return presets[0][1].isoformat()
        d = _parse_iso8601_date(raw)
        if d is None:
            print("Invalid date. Use YYYY-MM-DD.")
            continue
        if d < today:
            print("Expiry must be today or in the future.")
            continue
        if d > max_date:
            print("Expiry must be at most 1 year from today.")
            continue
        return d.isoformat()


def _write_rcfile_with_pat(
    rc_file_path: Path,
    api_url: str,
    pat: str,
    existing_config: Optional[Dict[str, str]] = None,
) -> None:
    """Write or update rcfile with ZPOOL_API_URL and ZPOOLPAT; chmod 0o600."""
    rc_file_path = Path(rc_file_path)
    rc_file_path.parent.mkdir(parents=True, exist_ok=True)

    def escape_value(v: str) -> str:
        if "\n" in v or '"' in v or " " in v:
            return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return v

    api_line = f"ZPOOL_API_URL={escape_value(api_url)}"
    pat_line = f"ZPOOLPAT={escape_value(pat)}"

    if existing_config is not None and rc_file_path.exists():
        lines = rc_file_path.read_text(encoding="utf-8").splitlines()
        seen_api = False
        seen_pat = False
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("ZPOOL_API_URL="):
                new_lines.append(api_line)
                seen_api = True
                continue
            if stripped.startswith("ZPOOLPAT="):
                new_lines.append(pat_line)
                seen_pat = True
                continue
            new_lines.append(line)
        if not seen_api:
            new_lines.append(api_line)
        if not seen_pat:
            new_lines.append(pat_line)
        rc_file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    else:
        comment_lines = [
            "",
            "# Full reference: https://github.com/zpools-io/zpools-io-client/blob/main/docs/configuration.md",
            "# Optional: SSH_HOST, SSH_PRIVKEY_FILE, etc.",
        ]
        rc_file_path.write_text(
            "\n".join([api_line, pat_line] + comment_lines) + "\n",
            encoding="utf-8",
        )
    rc_file_path.chmod(0o600)


def _has_existing_config(existing_config: Optional[Dict[str, str]]) -> bool:
    """True if we are updating an existing config file (vs creating from scratch)."""
    if existing_config is None:
        return False
    # Any meaningful key from the rc file indicates existing config (e.g. api_url, ssh_host, etc.)
    return bool(existing_config)


def run_pat_configure_wizard(
    rc_file_path: Path,
    console,
    existing_config: Optional[Dict[str, str]] = None,
    plaintext: bool = False,
) -> bool:
    """
    PAT-only configure flow: build dashboard URL, open browser, prompt for pasted PAT, write rcfile.
    Distinguishes "no config yet" vs "config exists but missing PAT" so we don't imply overwriting.
    If plaintext is True, use plaintext prompts (no Rich UI). Returns True if config was written.
    When stdin is not a TTY, does not prompt; returns False and prints a short error (for CI/scripts).
    """
    if not sys.stdin.isatty():
        if not _has_existing_config(existing_config):
            console.print(
                f"[red]Config file not found: {rc_file_path}. "
                "Run 'zpcli login' or create the file manually (see --help).[/red]"
            )
        else:
            console.print(
                f"[red]Config file has no ZPOOLPAT: {rc_file_path}. "
                "Run 'zpcli login' or add ZPOOLPAT to the file.[/red]"
            )
        return False

    has_existing = _has_existing_config(existing_config)
    if has_existing:
        console.print(
            "[yellow]Your config file exists but no PAT (ZPOOLPAT) is set. "
            "Add a PAT to your existing config? Other settings will be kept.[/yellow]"
        )
        sys.stdout.write("Add PAT now? [y/N]: ")
    else:
        console.print(
            "[yellow]You don't have a config file yet. "
            "Create one now? We'll set the API URL and add a PAT.[/yellow]"
        )
        sys.stdout.write("Create config now? [y/N]: ")
    sys.stdout.flush()
    create = input().strip().lower()
    if create not in ("y", "yes"):
        if has_existing:
            console.print(
                "Add ZPOOLPAT=your_token to your config file manually, or run [bold]zpcli login[/bold] to try again."
            )
        else:
            console.print(
                "Run zpcli again when you have a PAT, or create one at the dashboard and set ZPOOLPAT in your config."
            )
        return False

    # 1. API domain: pre-fill from existing config when updating
    default_api_url = "https://api.zpools.io/v1"
    if has_existing and (existing_config or {}).get("api_url"):
        default_api_url = (existing_config or {}).get("api_url", default_api_url)
    sys.stdout.write(f"\nAPI domain [{default_api_url}]: ")
    sys.stdout.flush()
    raw = input().strip()
    api_url = raw or default_api_url
    if not api_url.startswith("http"):
        api_url = "https://" + api_url
    if not _is_valid_api_url(api_url):
        api_url = default_api_url

    # 2. Label and scopes (for URL pre-fill)
    default_label = "CLI - laptop"
    sys.stdout.write(f"PAT label for the website form [{default_label}]: ")
    sys.stdout.flush()
    label_raw = input().strip()
    label = label_raw if label_raw else default_label
    if plaintext:
        print("\nPAT scopes:")
        scopes = _prompt_scopes_plaintext(console)
        print("\nPAT expiry:")
        expiry = _prompt_expiry_plaintext(console)
    else:
        console.print("\nSelect PAT scopes (↑/↓ move, Space toggle, Enter on Accept to confirm):")
        scopes = _prompt_scopes_interactive(console)
        console.print("\nSelect PAT expiry (↑/↓ move, Enter to select, max 1 year):")
        expiry = _prompt_expiry_interactive(console)

    # 3. Build URL and print / open
    url = _build_tokens_url(api_url, label=label, scopes=scopes, expiry=expiry)
    console.print(f"\n[bold]Open this URL to create a PAT:[/bold]\n  {url}")
    sys.stdout.write("Open in browser? [Y/n]: ")
    sys.stdout.flush()
    open_browser = input().strip().lower()
    if open_browser not in ("n", "no"):
        try:
            webbrowser.open(url)
        except Exception:
            console.print("[dim]Could not open browser; copy the URL above.[/dim]")

    # 4. Prompt for PAT (masked)
    pat = getpass.getpass("Paste your PAT (value will not be echoed): ").strip()
    if not pat:
        console.print("[red]No PAT entered. Configuration cancelled.[/red]")
        return False

    # 5. Write rcfile (merge into existing when has_existing)
    _write_rcfile_with_pat(rc_file_path, api_url, pat, existing_config=existing_config)
    if has_existing:
        console.print(f"[green]Updated config (added PAT)[/green] {rc_file_path}")
    else:
        console.print(f"[green]Wrote config to[/green] {rc_file_path}")

    # 6. Validate PAT with GET /hello
    console.print("Validating PAT...")
    try:
        from zpools import ZPoolsClient
        from zpools._generated.api.authentication import get_hello
        client = ZPoolsClient(api_url=api_url, pat=pat)
        auth_client = client.get_authenticated_client()
        response = get_hello.sync_detailed(client=auth_client)
        if response.status_code == 200:
            console.print("[green]PAT validated successfully.[/green]")
        else:
            console.print("[yellow]PAT was saved but validation returned a non-200 response.[/yellow]")
    except Exception as e:
        console.print("[yellow]PAT was saved but could not be validated.[/yellow]")
        console.print(f"[dim]{e}[/dim]")

    return True


def run_config_wizard(rc_file_path: Path, console) -> bool:
    """
    Interactively create a new rc file. Returns True if the file was written, False if the user declined.
    """
    console.print("[yellow]It doesn't look like you've got a config file.[/yellow]")
    create = input("Would you like to make one now? [y/N]: ").strip().lower()
    if create not in ("y", "yes"):
        console.print("Run zpcli again when you have a config file at the default path or use --rcfile.")
        return False

    # ZPOOL_USER: required, no default
    while True:
        username = input("zpools.io username (required): ").strip()
        if username:
            break
        console.print("[red]Username is required.[/red]")

    # Token cache: 1=no cache, 2=/dev/shm/zpools.io, or custom path
    console.print(
        "\nToken cache directory: JWT tokens can be cached so you don't re-enter your password."
    )
    console.print(
        "  [dim]1 = No cache (most secure; you will be prompted for password when needed)[/dim]"
    )
    console.print(
        "  [dim]2 = /dev/shm/zpools.io (ephemeral RAM-backed cache; faster, still not on disk)[/dim]"
    )
    console.print("  [dim]Or type another path to use as the cache directory.[/dim]")
    choice = input("Choice [1]: ").strip() or "1"

    token_cache_dir: Optional[str] = None
    if choice == "1":
        token_cache_dir = None
    elif choice == "2":
        token_cache_dir = "/dev/shm/zpools.io"
    else:
        token_cache_dir = choice.strip()

    if token_cache_dir:
        cache_path = Path(token_cache_dir).expanduser()
        if not cache_path.exists():
            create_dir = input(f"Directory {cache_path} does not exist. Create it? [y/N]: ").strip().lower()
            if create_dir in ("y", "yes"):
                cache_path.mkdir(parents=True, mode=0o700)
                console.print(f"[green]Created[/green] {cache_path} with permissions 0700.")
            else:
                console.print("[yellow]Skipping cache directory creation; token cache will not be used until the path exists.[/yellow]")
                token_cache_dir = None
        elif not cache_path.is_dir():
            console.print(f"[red]{cache_path} is not a directory; skipping token cache.[/red]")
            token_cache_dir = None

    # SSH private key: create new (default) or use existing; we require a valid key pair before writing rc file
    ssh_privkey_file: Optional[str] = None
    console.print("\nSSH key for ZFS over SSH (required):")
    console.print("  [dim]1 = Create a new key (default)[/dim]")
    console.print("  [dim]2 = Use an existing key[/dim]")
    key_choice = input("Choice [1]: ").strip().lower() or "1"

    if key_choice == "1":
        # Create new: show command, user runs it; Enter = default path, re-ask until valid key pair exists
        console.print(f"\nRun this command in another terminal (tune to your preferences), then return here:")
        console.print(f"  [bold]{DEFAULT_SSH_KEYGEN_CMD}[/bold]")
        default_resolved = str(Path(DEFAULT_SSH_KEY_PATH).expanduser())
        while True:
            raw_path = input(f"Path to the key you created [{default_resolved}]: ").strip()
            key_path = Path(raw_path).expanduser() if raw_path else Path(default_resolved)
            pub_path = Path(str(key_path) + ".pub")
            if key_path.exists() and key_path.is_file() and pub_path.exists() and pub_path.is_file():
                ssh_privkey_file = str(key_path)
                console.print(f"[green]Found key pair[/green] {key_path} / {pub_path}")
                break
            console.print(f"[red]No key pair at {key_path} (expected {pub_path}). Enter the path again.[/red]")
    else:
        # Use existing: list ~/.ssh keys or accept path; require valid key pair
        ssh_dir = Path.home() / ".ssh"
        skip_names = {"config", "known_hosts", "authorized_keys", "known_hosts.old"}
        private_keys: list[Path] = []
        if ssh_dir.exists() and ssh_dir.is_dir():
            try:
                for p in sorted(ssh_dir.iterdir()):
                    if p.is_file() and not p.name.endswith(".pub") and p.name not in skip_names:
                        private_keys.append(p)
            except OSError:
                pass
        if private_keys:
            for i, p in enumerate(private_keys, 1):
                console.print(f"  [dim]{i}. {p}[/dim]")
            console.print("  [dim]Or type a path to a different key.[/dim]")
        while True:
            if private_keys:
                raw = input("Choice or path: ").strip()
            else:
                raw = input("Path to SSH private key: ").strip()
            if not raw:
                console.print("[red]A valid SSH key pair is required. Enter a choice or path.[/red]")
                continue
            if raw.isdigit() and private_keys:
                idx = int(raw)
                if 1 <= idx <= len(private_keys):
                    key_path = private_keys[idx - 1]
                else:
                    console.print(f"[red]Invalid choice. Enter 1–{len(private_keys)} or a path.[/red]")
                    continue
            else:
                key_path = Path(raw).expanduser()
            pub_path = Path(str(key_path) + ".pub")
            if key_path.exists() and key_path.is_file() and pub_path.exists() and pub_path.is_file():
                ssh_privkey_file = str(key_path)
                console.print(f"[green]Found key pair[/green] {key_path} / {pub_path}")
                break
            console.print(f"[red]No key pair at {key_path} (expected {pub_path}). Try again.[/red]")

    if not ssh_privkey_file:
        console.print("[red]A valid SSH key pair is required to create the config file. Run the wizard again when you have one.[/red]")
        return False

    # Write rc file
    rc_file_path = Path(rc_file_path)
    rc_file_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"ZPOOL_USER={username}"]
    if token_cache_dir:
        lines.append(f"ZPOOL_TOKEN_CACHE_DIR={token_cache_dir}")
    if ssh_privkey_file:
        lines.append(f"SSH_PRIVKEY_FILE={ssh_privkey_file}")
    optional_overrides = [
        "",
        "# Full reference: https://github.com/zpools-io/zpools-io-client/blob/main/docs/configuration.md",
        "# Optional overrides (uncomment and set as needed):",
        "# 1. ZPOOL_API_URL=https://api.zpools.io/v1",
        "# 2. SSH_HOST=ssh.zpools.io",
    ]
    if not ssh_privkey_file:
        optional_overrides.append("# 3. SSH_PRIVKEY_FILE=path/to/private/key")
    optional_overrides.append("# 4. ZPOOLPAT=personal_access_token")
    if not token_cache_dir:
        optional_overrides.append(
            "# 5. ZPOOL_TOKEN_CACHE_DIR=path/to/cache/dir  (set to enable JWT caching; unset = no cache)"
        )
    optional_overrides.extend([
        "# 6. BZFS_BIN=path/to/bzfs",
        "# 7. LOCAL_POOL=your/local/zpool/dataset",
        "# 8. REMOTE_POOL=user@ssh.zpools.io:remote-zpool-id/remote-dataset",
        "",
        "",
    ])
    lines.extend(optional_overrides)

    rc_file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(f"[green]Wrote config to[/green] {rc_file_path}")
    return True


def load_rc_file(rc_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load configuration from zpoolrc file.
    
    Args:
        rc_path: Path to RC file. If None, uses ~/.config/zpools.io/zpoolrc
        
    Returns:
        Dictionary of configuration values
    """
    config = {}
    
    if rc_path:
        target = rc_path
    else:
        target = Path.home() / ".config" / "zpools.io" / "zpoolrc"
    
    if target.exists():
        # Simple shell-like parsing: KEY="VALUE" or KEY=VALUE
        with open(target, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    # Strip quotes if present
                    val = val.strip('"').strip("'")
                    config[key.strip()] = val
    
    return config


def get_config_value(
    key: str,
    explicit: Optional[str] = None,
    rc_config: Optional[Dict[str, str]] = None,
    default: Optional[str] = None
) -> Optional[str]:
    """
    Get configuration value with priority: explicit > env var > RC file > default.
    
    Args:
        key: Configuration key (also used as env var name)
        explicit: Explicitly provided value (highest priority)
        rc_config: RC file config dictionary
        default: Default value if not found elsewhere
        
    Returns:
        Configuration value or None
    """
    if explicit is not None:
        return explicit
    
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    
    if rc_config and key in rc_config:
        return rc_config[key]
    
    return default


def build_client_config(
    api_url: Optional[str] = None,
    username: Optional[str] = None,
    pat: Optional[str] = None,
    ssh_host: Optional[str] = None,
    ssh_privkey: Optional[str] = None,
    token_cache_dir: Optional[str] = None,
    rc_file: Optional[Path] = None
) -> Dict[str, str]:
    """
    Build configuration for ZPoolsClient by merging explicit values, env vars, and RC file.
    
    Priority for most values: explicit args > environment variables > RC file > defaults
    Password priority: ONLY from ZPOOL_PASSWORD environment variable (never CLI arg or RC file)
    
    Args:
        api_url: Explicit API URL
        username: Explicit username
        pat: Explicit PAT token
        ssh_host: Explicit SSH host
        ssh_privkey: Explicit SSH private key path
        token_cache_dir: Explicit token cache base directory
        rc_file: Path to RC file (default: ~/.config/zpools.io/zpoolrc)
        
    Returns:
        Dictionary with resolved configuration values
    """
    # Load RC file if needed
    rc_config = load_rc_file(rc_file)
    
    # Build config with priority chain (explicit > env > RC > default)
    config = {
        "api_url": get_config_value("ZPOOL_API_URL", api_url, rc_config, "https://api.zpools.io/v1"),
        "username": get_config_value("ZPOOL_USER", username, rc_config),
        "pat": get_config_value("ZPOOLPAT", pat, rc_config),
        "ssh_host": get_config_value("SSH_HOST", ssh_host, rc_config, "ssh.zpools.io"),
        "ssh_privkey": get_config_value("SSH_PRIVKEY_FILE", ssh_privkey, rc_config),
        "token_cache_dir": get_config_value("ZPOOL_TOKEN_CACHE_DIR", token_cache_dir, rc_config),
    }
    
    # Password: ONLY from environment variable (never CLI arg or RC file)
    config["password"] = os.getenv("ZPOOL_PASSWORD")
    
    return config
