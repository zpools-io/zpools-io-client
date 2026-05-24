# CLI troubleshooting

CLI-specific errors and fixes. For conceptual causes (auth, SSH, jobs, etc.), see the top-level [Troubleshooting](../../../../docs/troubleshooting.md).

## Exit codes

- **0** — Success.
- **1** — General error (e.g. validation, config, or request failure). Check the message printed by `zpcli`.
- **3** — Watch timeout. The requested `--watch` did not observe completion before its timeout; the underlying job or EBS modification may still be running.
- Non-zero from ZFS/SSH — Propagated from the underlying command (e.g. `zfs` or `ssh`).

## Common CLI messages

- **"ZPOOL_USER not configured" / "SSH_HOST not configured" / "SSH_PRIVKEY_FILE not configured"**  
  Set the missing key in `~/.config/zpools.io/zpoolrc` or via environment. See [Configuration](../../../../docs/configuration.md#required-parameters).

- **"SSH private key not found"**  
  Ensure `SSH_PRIVKEY_FILE` points to an existing key file with correct permissions (e.g. 600).

- **Authentication failed**  
  Check username and password (or PAT). Use a PAT for non-interactive use. See [Authentication](../../../../docs/authentication.md#using-a-pat).

- **Request errors**  
  The CLI prints the error message. For job-related issues see [Async jobs](../../../../docs/reference/async-jobs.md) and use `zpcli job get <job_id>` to inspect.

## Tab completion

- If completion does not work after `zpcli completion --install`, restart your shell or source your rc file.
- Tab completion is not available when using `uv run zpcli`; use `uv tool install --editable packages/cli` for full support.

## See also

- [Top-level troubleshooting](../../../../docs/troubleshooting.md) — Auth, rcfile, SSH, job timeouts, ZFS, non-interactive PAT.
- [Installation](installation.md) | [Command reference](commands.md)
