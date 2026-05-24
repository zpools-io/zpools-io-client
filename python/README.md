# zpools.io Python Workspace

This directory contains the Python SDK and CLI (`zpcli`) for zpools.io.

## Documentation

- **Top-level docs:** [../docs/](../docs/README.md) — quickstart, configuration, authentication, reference, troubleshooting (language-independent).
- **CLI:** [packages/cli/README.md](packages/cli/README.md) — Installation, command reference, troubleshooting.
- **SDK:** [packages/sdk/README.md](packages/sdk/README.md) — Installation, quickstart, API reference, troubleshooting.

## Prerequisites

- **Python 3.9+**
- **uv** (recommended): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Ensure `~/.local/bin` is in your PATH.

## Install CLI (recommended)

```bash
cd python
uv tool install --editable packages/cli
```

Then: `zpcli completion --install` (optional), `zpcli --help`. Tab completion works with the installed `zpcli`; use the CLI [installation guide](packages/cli/docs/installation.md) for pip and options.

## Alternative: uv run

```bash
cd python
uv sync
uv run zpcli --help
```

Tab completion does not work with `uv run zpcli`.

## Development

- **SDK source:** `packages/sdk/src/zpools`
- **CLI source:** `packages/cli/src/zpools_cli`

## Testing

Automated tests in this repo target only the CLI and SDK packages under `python/packages/`. They use mocks and do not perform network I/O. They are not substitutes for backend or full-stack tests, which live elsewhere.

Run CLI tests from the repository root:

```bash
PYTHONPATH="$PWD/python/packages/cli/src:$PWD/python/packages/sdk/src" uv run pytest python/packages/cli/tests/unit -q
```

Run this before changing CLI command wiring, option defaults, exit codes, or user-visible output. SDK tests are not present yet; when added, they should follow the same no-network default.
