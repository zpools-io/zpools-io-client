# zpools-cli

The official command line interface for zpools.io. Use `zpcli` to manage zpools, jobs, SSH keys, billing, and ZFS over SSH.

## Installation

```bash
cd python
uv tool install --editable packages/cli
```

Ensure `~/.local/bin` is in your PATH. See [Installation](docs/installation.md) for pip, prerequisites (Python 3.9+, uv), and options.

## Minimal usage

```bash
zpcli --help
zpcli zpool list
zpcli zpool create --size 125 --volume-type gp3 --watch
zpcli billing balance
zpcli sshkey list
```

**Configuration:** Create `~/.config/zpools.io/zpoolrc` with `ZPOOL_USER`, `ZPOOL_API_URL`; for ZFS add `SSH_HOST` and `SSH_PRIVKEY_FILE`. See the [top-level docs](../../../docs/README.md) for [configuration](../../../docs/configuration.md), [authentication](../../../docs/authentication.md), [quickstart](../../../docs/quickstart.md), and [reference](../../../docs/reference/storage-units.md).

## Documentation

- **This package:** [Installation](docs/installation.md) | [Command reference](docs/commands.md) | [Troubleshooting](docs/troubleshooting.md)
- **Top-level (language-independent):** [docs/](../../../docs/README.md) — quickstart, configuration, authentication, reference (storage units, async jobs), troubleshooting

## Development

Editable install reflects code changes immediately. For `uv run` without global install: `cd python && uv sync && uv run zpcli --help`. Tab completion works with the installed `zpcli`, not with `uv run zpcli`.
