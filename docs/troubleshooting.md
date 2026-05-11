# Troubleshooting

This page covers **conceptual** causes and fixes. For tool-specific errors (exit codes, CLI messages, SDK exceptions), see the package docs linked below.

## Authentication failures

- **Wrong credentials:** Verify username and password (or PAT). For PAT, ensure it has the right scopes and has not been revoked.
- **Missing rcfile or env:** Ensure `ZPOOL_USER` and either password (interactive) or PAT (non-interactive) are set. See [Configuration](configuration.md#required-parameters) and [Authentication](authentication.md#pat).
- **Token expired:** JWT tokens are short-lived. If you see auth errors after a long idle period, log in again or use a PAT.
- **Testing auth:** To validate credentials without running a full operation, use `zpcli hello` — it is intended to test connectivity and authenticate. See the [CLI command reference](../python/packages/cli/docs/commands.md) (hello command).

## Missing rcfile or environment

- Create `~/.config/zpools.io/zpoolrc` with at least `ZPOOL_USER`. For ZFS over SSH add `SSH_PRIVKEY_FILE`.
- Or set the same keys via environment variables (env overrides rcfile). Example: `export ZPOOL_USER=myuser`. See [Configuration](configuration.md#environment-overrides) for all keys and examples.

## SSH issues

- **Key not found or wrong permissions:** Ensure `SSH_PRIVKEY_FILE` points to a valid private key file with correct permissions (e.g. 600).
- **Host/key mismatch:** Confirm you use the same account and key registered with zpools.io (SSH keys added via CLI or SDK).
- **Connection refused or timeout:** Check network, firewall, and that `SSH_HOST` (e.g. `ssh.zpools.io`) is correct.

## Job timeouts

- Some operations (create zpool, modify, scrub) are **asynchronous** and return a job ID. If you wait for completion, the client polls until the job finishes or a timeout is reached.
- **Timeout too short:** Increase the watch timeout if your operation is slow (see [Async jobs](reference/async-jobs.md#polling-and-timeouts)). CLI: use `--watch` and check for timeout options in the [command reference](../python/packages/cli/docs/commands.md).
- **Job failed:** Inspect job status (CLI: `zpcli job get <job_id>`; SDK: `get_job`). See [reference/async-jobs.md](reference/async-jobs.md).

## ZFS errors

- Destructive ZFS operations (e.g. destroy) are your responsibility. Confirm datasets and snapshots before running them.
- If a ZFS command fails over SSH, check SSH connectivity and that the remote pool/dataset exists and you have permission.

## Non-interactive use (CI/CD, scripts)

- Use a **PAT** instead of username/password. Set `ZPOOLPAT` (or equivalent) in the environment or pass it explicitly to the client.
- Do not rely on interactive prompts in automation. See [Authentication](authentication.md#using-a-pat).

## Package-specific troubleshooting

- **CLI:** Exit codes, `zpcli` error messages, and CLI-specific fixes: [python/packages/cli/docs/troubleshooting.md](../python/packages/cli/docs/troubleshooting.md).
- **SDK:** Exceptions (e.g. `UnexpectedStatus`), auth errors, timeouts, custom API URL: [python/packages/sdk/docs/troubleshooting.md](../python/packages/sdk/docs/troubleshooting.md).
