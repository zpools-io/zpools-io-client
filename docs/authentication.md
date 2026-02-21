# Authentication

The CLI uses **PAT (Personal Access Token)** only. The SDK supports both **PAT** and **JWT** (username/password) for server-side and integration use.

## CLI: PAT only

- The CLI does **not** prompt for username/password. Use a **Personal Access Token** (PAT).
- Get a PAT by signing in on the website and creating a token (Dashboard → Tokens), or run `zpcli login` to open the configure wizard: it will open the dashboard to create a PAT, then you paste the token into the CLI.
- Store the PAT in your rcfile or set `ZPOOLPAT` in the environment. Do not commit PATs to version control.
- For automation (CI/CD, scripts), use a PAT scoped with least privilege (e.g. `zpool` + `job` only).

### Using a PAT

Set `ZPOOLPAT` in your environment or add it to your rcfile (see [Configuration](configuration.md)). Then run any command:

```bash
export ZPOOLPAT="zpat_xxxxxxxxxxxxxxxxxxxxxxxx"
zpcli hello  # Confirms the PAT works
```

Or run the login wizard to configure interactively:

```bash
zpcli login
```

The wizard opens the dashboard to create a PAT (if needed), then you paste the token; it is written to your rcfile.

### Managing PATs

Create and revoke PATs on the **website** (Dashboard → Tokens). The CLI commands `zpcli pat list` and `zpcli pat revoke` work with your existing PAT; create new PATs on the dashboard (no CLI command).

## SDK: PAT and JWT

The SDK supports both PAT and JWT so that server-side code and integration tests can use username/password where appropriate. For production automation, prefer PAT with limited scopes.

- **PAT:** Pass a PAT to the client (e.g. env `ZPOOLPAT` or client argument). Same as CLI.
- **JWT:** Use username and password; the SDK can call the login endpoint and cache tokens. Password is not read from the rcfile; use `ZPOOL_PASSWORD` env or prompt. For integration tests and internal tools only; the **login endpoint is disabled in production**.

## PAT scopes

When creating a PAT on the website you choose scopes. If you omit scopes, the token has no access.

| Scope     | Purpose |
|----------|---------|
| `*`      | All features (full access). Same access as your user account. |
| `zpool`  | List, create, delete, modify, scrub zpools. |
| `job`    | List jobs, get job details, get job history. |
| `sshkey` | List, add, delete SSH keys. |
| `pat`    | List and revoke PATs (create is on the website). |
| `billing`| Billing balance, ledger, summary. Add credits and redeem codes on the dashboard. |

**Scope strategies:**

- **Full access:** Use `*` when you need unrestricted access.
- **Least privilege:** Grant only the scopes needed (e.g. `zpool` + `job` for CI that manages pools).
- **Short-lived:** Combine limited scopes with an expiry date for temporary automation.

## rcfile and environment

The CLI and SDK read configuration from an rcfile and/or environment variables. For the CLI, the important key is **`ZPOOLPAT`** (or the wizard writes it). For the SDK, `ZPOOL_USER`, `ZPOOL_PASSWORD`, and `ZPOOL_TOKEN_CACHE_DIR` are used when using JWT. See [Configuration](configuration.md).

## See also

- [Configuration](configuration.md) — rcfile path and keys.
- [Troubleshooting](troubleshooting.md#authentication-failures) — Auth failures, non-interactive PAT.
- CLI: auth behavior in [command reference](../python/packages/cli/docs/commands.md) and [troubleshooting](../python/packages/cli/docs/troubleshooting.md).
- SDK: auth in [quickstart](../python/packages/sdk/docs/quickstart.md) and [API reference](../python/packages/sdk/docs/api-reference.md).
