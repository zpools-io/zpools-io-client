# Command reference

`zpcli` is the official zpools.io CLI. All commands use configuration from `~/.config/zpools.io/zpoolrc` (or `--rcfile`) and environment variables. See [Configuration](../../../../docs/configuration.md) and [Authentication](../../../../docs/authentication.md).

## Global options

- `--rcfile <path>` — Use a different rcfile (default: `~/.config/zpools.io/zpoolrc`).

## Top-level commands

- `zpcli hello` — Test connectivity and authentication.
- `zpcli version` — Show CLI version.
- `zpcli completion --install` — Install shell completion (bash, zsh, fish, powershell).

## Command groups

- **[SSH keys](commands-sshkey.md)** — `zpcli sshkey` — List, add, delete SSH public keys. Required for ZFS over SSH.
- **[Billing](commands-billing.md)** — `zpcli billing` — Balance, ledger, summary, claim codes.
- **[Personal Access Tokens](commands-pat.md)** — `zpcli pat` — List, create, revoke PATs. Use for non-interactive/CI.
- **[Jobs](commands-job.md)** — `zpcli job` — List, get, history. Async operations return a job ID; use these to poll.
- **[Zpools](commands-zpool.md)** — `zpcli zpool` — List, create, delete, modify, scrub. Sizes in GiB; many operations are async.
- **[ZFS over SSH](commands-zfs.md)** — `zpcli zfs` — List, snapshot, destroy, recv, ssh. Requires SSH config.

## Auth and async

- **Auth:** Commands that need auth use JWT (interactive prompt or env) or PAT. See [Authentication](../../../../docs/authentication.md).
- **Async vs sync:** Commands like `zpool create`, `zpool modify`, and `zpool scrub` run asynchronously. Create and scrub return job IDs; volume type modifications are tracked through zpool volume state. Use `--watch` to poll until completion. See [Async jobs](../../../../docs/reference/async-jobs.md).

## Tab completion

Shell tab completion is supported for **bash**, **zsh**, **fish**, and **powershell**. Install once per shell:

```text
zpcli completion --install
```

Restart your shell (or source your rc file, e.g. `source ~/.bashrc`) so the completion script is loaded. After that, typing `zpcli ` and pressing Tab will complete top-level commands and subcommands; subcommand-specific completion (e.g. options and arguments) is available where implemented.

**Note:** Completion is not available when you run the CLI via `uv run zpcli`; use `uv tool install --editable packages/cli` so `zpcli` is on your PATH for full support. Some commands do not yet complete arguments (e.g. file paths for `zpcli sshkey add`). If completion does not work after install, see [Troubleshooting](troubleshooting.md#tab-completion).

## See also

- [Configuration](../../../../docs/configuration.md)
- [Troubleshooting](troubleshooting.md) (CLI-specific) and [top-level troubleshooting](../../../../docs/troubleshooting.md)
