# Quickstart: Your first zpool

This guide uses the **CLI** (`zpcli`) for every step. Have the CLI installed, then run the commands below to create your first zpool. We do not recommend using the SDK alone for this quickstart—use the CLI.

The steps below are intended to **validate the service**: they mirror the important parts of the integration tests (zpool create, ZFS send/recv round-trip, content comparison) in a human-readable form. The ZFS examples use **small datasets and snapshots** to prove accuracy and reliability while **minimizing data transfer**. Pulling data from the remote service to your machine (egress) incurs **AWS egress charges**, which are cost-prohibitive; the validation flow below keeps egress small and is **not intended for production backup or restore**.

---

## 1. Sign up

Create an account at **https://zpools.io**. You will get a **username**; you need it for the next steps.

---

## 2. Install the CLI

Install the CLI (Python 3.9+, **uv** or **pip**). See **[CLI Installation](../python/packages/cli/docs/installation.md)** for step-by-step install, PATH setup, and first-time options (tab completion, rcfile). The CLI is not yet on PyPI; install from the repo as described there.

Verify:

```bash
zpcli --help
zpcli version
```

---

## 3. Configure

Configuration is stored in an rcfile at `~/.config/zpools.io/zpoolrc` (or a path you pass with `--rcfile`). The CLI uses a **Personal Access Token (PAT)** only. For the full set of options, see [Configuration](configuration.md).

**Easiest:** Run `zpcli login`. The wizard will open the dashboard so you can sign in and create a PAT, then you paste the token into the CLI. It will also prompt for API URL (default `https://api.zpools.io/v1`), label, scopes, expiry, and SSH key (create new or use existing). The wizard writes the rcfile. Alternatively, run a command that needs config (e.g. `zpcli hello`); if you have no config or no PAT, the same wizard runs.

**Manual:** Create a PAT on the website (Dashboard → Tokens), then create the rcfile with your PAT and SSH key path:

```bash
mkdir -p ~/.config/zpools.io
printf '%s\n' 'ZPOOLPAT=zpat_xxxxxxxxxxxxxxxxxxxxxxxx' 'SSH_PRIVKEY_FILE=~/.ssh/id_ed25519' > ~/.config/zpools.io/zpoolrc
```

**ZFS over SSH** (required for steps 7–10): If you did not set an SSH key in the wizard, edit the rcfile and set your SSH private key path (and optionally `SSH_HOST`; it defaults to `ssh.zpools.io`).

Verify connectivity and auth:

```bash
zpcli hello
```

---

## 4. Claim a beta code (if required)

> **Beta:** During beta, a **beta invite code** is required to activate your account. Check [Discord](https://zpools.io/discord) for beta access and support. This step will not be required after general availability.

Redeem your code on the **dashboard Billing page**. Sign in at [zpools.io](https://zpools.io), go to Dashboard → Billing, and use the claim section to enter your code.

---

## 5. SSH key upload

Upload the public key you set in the config wizard (or in your rcfile as `SSH_PRIVKEY_FILE`) so the service can use it for ZFS over SSH. Use the path from your rcfile; the public key is the same path with `.pub` appended.

```bash
KEY_PATH=$(grep -E '^SSH_PRIVKEY_FILE=' ~/.config/zpools.io/zpoolrc | cut -d= -f2- | tr -d '"')
test -n "$KEY_PATH" && test -f "${KEY_PATH}.pub" && zpcli sshkey add "${KEY_PATH}.pub"
```

Confirm the key is listed:

```bash
zpcli sshkey list
```

---

## 6. Create a zpool

> **Beta:** During beta, zpools are limited to **125 GiB** and **one zpool per user**. These limits will be relaxed after general availability.

Create a zpool and watch it finish so you have a remote zpool for the validation steps below. Assign the size and type to variables so later steps can refer to them; then create and capture the zpool ID from the list.

```bash
SIZE_GIB=125
VOL_TYPE=gp3
test -n "$SIZE_GIB" && test -n "$VOL_TYPE" && zpcli zpool create --size "$SIZE_GIB" --volume-type "$VOL_TYPE" --watch
```

When it completes, list your zpools and set `ZPOOL_ID` from the output (use the ID shown for your new zpool):

```bash
zpcli zpool list
ZPOOL_ID=your-zpool-id-here
```

Use the ID in later steps:

```bash
test -n "$ZPOOL_ID" && zpcli zfs list "$ZPOOL_ID"
```

If you ran create without `--watch`, poll by job ID:

```bash
JOB_ID=your-job-id
test -n "$JOB_ID" && zpcli job get "$JOB_ID"
test -n "$ZPOOL_ID" && zpcli zpool list
```

---

## 7. Create a local snapshot (validation dataset)

The following steps (7–10) **validate** the service with small datasets and snapshots. They are for proving accuracy and reliability, **not** for production use. **Egress** (data transferred from the service to your machine) is **AWS-billed and cost-prohibitive**; keep validation traffic small and avoid large egress in normal use.

You need a **local ZFS pool** (e.g. `rpool` or `tank`) and `sudo` for local `zfs` commands. Replace `rpool` with your local pool name if different.

Create a small local dataset, add a tiny file, and snapshot it. Use variables so commands are copy-pastable and safe.

```bash
LOCAL_POOL=rpool
SUFFIX=$(date +%s)-$$
LOCAL_DS="${LOCAL_POOL}/zpools-validate-${SUFFIX}"
REMOTE_DS="${ZPOOL_ID}/validate-${SUFFIX}"
```

Create the local dataset and a minimal file:

```bash
test -n "$LOCAL_DS" && sudo zfs create "$LOCAL_DS"
MP=$(sudo zfs get -H -o value mountpoint "$LOCAL_DS")
test -n "$MP" && echo "validate-content" | sudo tee "${MP}/tiny.txt" > /dev/null
```

Create the first snapshot:

```bash
SNAP1="${LOCAL_DS}@v1"
test -n "$SNAP1" && sudo zfs snapshot "$SNAP1"
```

## 8. Send the local snapshot to the remote zpool

Pipe a full send from your machine into the CLI so the stream is received on the remote zpool. This sends data **to** the service (ingress); cost impact is typically low.

```bash
test -n "$SNAP1" && test -n "$REMOTE_DS" && sudo zfs send "$SNAP1" | zpcli zfs recv "$REMOTE_DS"
```

## 9. Retrieve the remote snapshot into a local copy

Receive the same snapshot **from** the remote back to a new local dataset. This causes **egress** from the service; we do it once with a tiny snapshot only to validate correctness.

```bash
RECV_DS="${LOCAL_DS}-recv"
```

You need to run `zfs send` on the remote and pipe it to local `zfs recv`. The CLI reads the rcfile; your shell does not. So set (or export) `ZPOOL_USER`, `SSH_PRIVKEY_FILE`, and `SSH_HOST` for the `ssh` command below—e.g. from `~/.config/zpools.io/zpoolrc` or manually:

```bash
# If your shell does not load the rcfile, set these (use the same values as in zpoolrc)
export ZPOOL_USER=your-username
export SSH_PRIVKEY_FILE=${SSH_PRIVKEY_FILE:-$HOME/.ssh/id_ed25519}
export SSH_HOST=${SSH_HOST:-ssh.zpools.io}
REMOTE_SNAP="${REMOTE_DS}@v1"
test -n "$REMOTE_SNAP" && test -n "$RECV_DS" && test -n "$ZPOOL_USER" && ssh -i "$SSH_PRIVKEY_FILE" "$ZPOOL_USER@$SSH_HOST" "sudo zfs send $REMOTE_SNAP" | sudo zfs recv "$RECV_DS"
```

## 10. Compare what was sent versus what was received

Verify the received dataset has the same content as the original. This confirms the send/recv round-trip preserved data.

```bash
RECV_MP=$(sudo zfs get -H -o value mountpoint "$RECV_DS")
test -n "$RECV_MP" && sudo cat "${RECV_MP}/tiny.txt"
```

Compare with the original:

```bash
test -n "$MP" && sudo cat "${MP}/tiny.txt"
```

Both should show `validate-content`. Optionally destroy the validation datasets and snapshot when done:

```bash
test -n "$RECV_DS" && sudo zfs destroy -r "$RECV_DS"
test -n "$LOCAL_DS" && sudo zfs destroy -r "$LOCAL_DS"
```

---

## Next steps

- [Configuration](configuration.md) — rcfile keys and environment overrides.
- [Authentication](authentication.md) — JWT vs PAT, token caching.
- [Async jobs](reference/async-jobs.md) — Job IDs and polling.
- [CLI command reference](../python/packages/cli/docs/commands.md) — All `zpcli` commands.
