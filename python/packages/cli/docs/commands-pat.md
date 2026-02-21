# Personal Access Token commands

`zpcli pat` — Manage Personal Access Tokens (PATs) via the CLI.

For PAT concepts and scopes, see [Authentication](../../../../docs/authentication.md#pat). PAT key IDs use the standard [Resource IDs](../../../../docs/reference/ids.md) format.

## Commands

| Command | Description |
|---------|-------------|
| `zpcli pat list` | List your PATs |
| `zpcli pat revoke <key_id>` | Revoke a PAT |

---

## list

```text
zpcli pat list [OPTIONS]
```

Lists all PATs for the authenticated user. The token secret is never shown after creation; only metadata is displayed.

**Output columns**

| Column | Description |
|--------|-------------|
| ID | Key ID (use with `pat revoke`). Four-word hyphenated format. |
| Label | Name you gave the token at creation. |
| Status | Current state (e.g. active, revoked). |
| Created At | Creation timestamp. |
| Expiry | Expiry date, or "Never". |
| Last Used | When the token was last used, or "Never". |
| Scopes | Comma-separated scopes (e.g. `zpool`, `job` or `*`). |

**Options**

| Option | Description |
|--------|-------------|
| `--json` | Output raw JSON instead of table. |
| `--local` | Show timestamps in local timezone (default: UTC). |

**Examples**

```text
zpcli pat list
zpcli pat list --local
zpcli pat list --json
```

---

## revoke

```text
zpcli pat revoke <key_id> [OPTIONS]
```

Revokes a PAT by key ID. Revocation is permanent and immediate.

**Argument**

| Argument | Description |
|----------|-------------|
| `key_id` | Key ID to revoke (e.g. `law-hotel-shape-community`). Get from `pat list`. |

**Options**

| Option | Description |
|--------|-------------|
| `--json` | Output raw JSON and skip confirmation prompt. |

**Confirmation**

Without `--json`, the CLI prompts for confirmation before revoking.

**Examples**

```text
zpcli pat revoke law-hotel-shape-community
zpcli pat revoke law-hotel-shape-community --json
```

---

## See also

- [Authentication](../../../../docs/authentication.md#pat) — PAT concepts, scopes, JWT vs PAT
- [Command reference](commands.md)
- [Resource IDs](../../../../docs/reference/ids.md) — Key ID format
