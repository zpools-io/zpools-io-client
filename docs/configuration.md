# Configuration

The zpools.io client (CLI and SDK) reads configuration from an **rcfile** and from **environment variables**. The same keys apply to both tools.

## rcfile path

- **Default:** `~/.config/zpools.io/zpoolrc`
- **CLI:** You can override with `--rcfile <path>`.
- **SDK:** Use the same path by default; override by passing explicit arguments when creating the client (see [SDK API reference](../python/packages/sdk/docs/api-reference.md)).

## Required parameters

| Key                | Purpose                                                                |
| ------------------ | ---------------------------------------------------------------------- |
| `ZPOOLPAT`         | Personal Access Token. (Required for CLI authenticated API access. Use `zpcli login` to configure.) |
| `SSH_PRIVKEY_FILE` | Path to your SSH private key file. (Required for SSH access)           |

**CLI:** The CLI uses only PAT. Set `ZPOOLPAT` in the rcfile or environment, or run `zpcli login` to run the configure wizard (it opens the dashboard to create a PAT, then you paste it).

**SDK:** The SDK can use PAT or JWT (username/password). For JWT, set `ZPOOL_USER` and use `ZPOOL_PASSWORD` in the environment. `ZPOOL_TOKEN_CACHE_DIR` is for JWT token caching. The login endpoint is disabled in production; use JWT only in dev/integration tests.

## Optional overrides

| Key | Purpose |
|-----|---------|
| `ZPOOL_API_URL` | API base URL. Default: `https://api.zpools.io/v1`. |
| `SSH_HOST` | SSH endpoint for ZFS over SSH. Default: `ssh.zpools.io`. |
| `ZPOOL_USER` | Username (SDK JWT only; not used by CLI). |
| `ZPOOL_TOKEN_CACHE_DIR` | JWT token cache directory (SDK only; not used by CLI). |

## BZFS parameters (optional)

| Key | Purpose |
|-----|---------|
| `BZFS_BIN` | Absolute path to `bzfs` for BzFS sync integration. |
| `LOCAL_POOL` | Local zpool/dataset for BzFS. |
| `REMOTE_POOL` | Remote target (e.g. `user@ssh.zpools.io:remote-zpool-id/remote-dataset`). |

**Password:** Used only by the SDK when using JWT (e.g. integration tests). Set `ZPOOL_PASSWORD` in the environment; it is not read from the rcfile. The CLI does not use username/password.

## Environment overrides

Environment variables override rcfile values. Commonly used:

- `ZPOOLPAT` — Personal Access Token (CLI and SDK; required for CLI auth)
- `ZPOOL_API_URL` — API endpoint
- `ZPOOL_USER` — Username (SDK JWT only)
- `ZPOOL_PASSWORD` — Password (SDK JWT only; env only)

See [Authentication](authentication.md) for CLI (PAT only) vs SDK (PAT or JWT).

## Example rcfile

```bash
ZPOOLPAT="zpat_xxxxxxxxxxxxxxxxxxxxxxxx"
SSH_PRIVKEY_FILE="/path/to/your/private/key"

# Optional overrides (defaults in effect if omitted):
# ZPOOL_API_URL="https://api.zpools.io/v1"
# SSH_HOST="ssh.zpools.io"

# Optional (BzFS sync):
# BZFS_BIN="/absolute/path/to/bzfs"
# LOCAL_POOL="your/local/zpool/dataset"
# REMOTE_POOL="user@ssh.zpools.io:remote-zpool-id/remote-dataset"
```

## See also

- [Authentication](authentication.md) — PAT (CLI) vs PAT/JWT (SDK).
- [Quickstart](quickstart.md) — First zpool flow.
- CLI: [installation](../python/packages/cli/docs/installation.md) and config usage.
- SDK: [installation](../python/packages/sdk/docs/installation.md) and client options.
