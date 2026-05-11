# Zpool commands

`zpcli zpool` — List, create, delete, modify, and scrub ZFS pools. Sizes are in **GiB**. Many operations are asynchronous and return a **job ID**; use `--watch` to poll until completion or use [job commands](commands-job.md) to check status.

See [Storage units](../../../../docs/reference/storage-units.md), [Async jobs](../../../../docs/reference/async-jobs.md), and [Resource IDs](../../../../docs/reference/ids.md) (zpool IDs).

**Asides:** In this document, we use blockquote asides to call out information that is separate from the main flow:

- **Beta:** Beta-specific limits, quotas, or behavior that may change after beta.
- **Note:** General clarifications or caveats.
- **Tip:** Optional guidance (e.g. when to use a flag).

## Commands

- `zpcli zpool list` — List your zpools with per-zpool volume details (size, type, state, modification status).
- `zpcli zpool create` — Create a zpool. Returns a job ID; use `--watch` to watch completion. Options: `--size`, `--volume-type` (gp3, sc1), `--watch`, `--resume`, `--timeout`, `--json`.
- `zpcli zpool delete <zpool_id>` — Delete a zpool. Options: `--json`.
- `zpcli zpool modify <zpool_id>` — Submit a volume type change (gp3 ↔ sc1). Returns a job ID; use `--watch` or `--wait-until-able`. Options: `--type`, `--watch`, `--wait-until-able`, `--resume`, `--timeout`, `--json`, `--local`.
- `zpcli zpool expand <zpool_id>` — Expand a zpool (not yet implemented). Options: `--size`, `--json`.
- `zpcli zpool scrub <zpool_id>` — Start a scrub. Returns a job ID; use `--watch` to watch completion. Options: `--watch`, `--resume`, `--timeout`, `--json`.

---

## list

```text
zpcli zpool list [--json]
```

Lists all zpools for the authenticated user. Each zpool is shown with a **per-zpool table of volumes**: size (GiB), type, state, modification state, progress, and whether the volume can be modified now (or when it will be eligible after the AWS cooldown).

**Output**

- **Default:** For each zpool: zpool ID (heading), user, volume count, created date, last scrub date; then a table of volumes with columns:
  - **Size (GiB)** — Volume size in GiB.
  - **Type** — EBS volume type (e.g. `gp3`, `sc1`).
  - **State** — Volume state (e.g. in-use, available).
  - **Mod State** — Modification state (e.g. completed, in-progress).
  - **Mod %** — Modification progress percentage (if applicable).
  - **Can Modify** — Whether the volume can be modified now (`Yes`), or `In ~Xh Ym` until cooldown expires, or `No`.

If you have no zpools, the CLI prints *No ZPools found.*

**Options**

- `--json` — Output raw JSON instead of the formatted tables.

**Examples**

```text
zpcli zpool list
zpcli zpool list --json
```

---

## create

```text
zpcli zpool create [OPTIONS]
```

Creates a new ZFS pool backed by EBS volumes. You get a **job ID** immediately; creation runs asynchronously. Use `--watch` to have the CLI poll until the job completes (or times out), or poll yourself with `zpcli job get <job_id>` / `zpcli job history <job_id>`.

> **Beta:** During beta, **only 125 GiB** zpools are allowed. If you pass a different size, the CLI reports an error. The default `--size` is 125.

> **Beta:** During beta, **one zpool per user**. If you already have a zpool, creating another fails with a message that a zpool already exists. Delete the existing zpool first if you want to create a new one.

**Options**

- `--size <n>` — Size in **GiB** for the new zpool. Default: **125**. During beta only 125 is accepted; other values are rejected. See [Storage units](../../../../docs/reference/storage-units.md).
- `--volume-type <type>` — EBS volume type. Default: **gp3**. Choices:
  - **gp3** — General Purpose SSD. Higher performance and cost; good for general use and when you need lower latency.
  - **sc1** — Cold HDD. Lower cost, suited for less frequently accessed data (e.g. backups, archives).
- `--watch` — After submitting the create job, poll until the job completes (succeeded or failed) or the timeout is reached. Without `--watch`, the command prints the job ID and exits; you can then use `zpcli job get <job_id>` or `zpcli job history <job_id>` to check status, or use `--resume` later to attach to the same job.
- `--resume` — Do not create a new zpool; instead, find an existing **zpool create** job for your account that is still in progress and monitor it until completion (or timeout). Useful if you ran `create` without `--watch` and want to reattach (e.g. after closing the terminal).
- `--timeout <seconds>` — Timeout in seconds when using `--watch` or `--resume`. Default: **1800** (30 minutes). If the job does not complete within this time, the CLI reports a timeout and exits; the job continues and you can still poll by job ID.
- `--json` — Output raw JSON instead of the formatted messages. With `--watch` or `--resume`, the final job state is printed as JSON.

**Success output (without `--watch`)**

- Message that zpool creation started.
- **Job ID** — Use this with `zpcli job get <job_id>` or `zpcli job history <job_id>`, or run `zpcli zpool create --resume` to reattach.

**Success output (with `--watch`)**

- Progress is shown while the CLI polls. On completion, the CLI prints the **ZPool ID** when available. If the job fails or times out, the CLI reports the outcome and the job ID.

**Examples**

```text
# Create a 125 GiB zpool with default type (gp3); get job ID and poll yourself
zpcli zpool create

# Create with explicit size and type; watch until completion (default 30 min timeout)
zpcli zpool create --size 125 --volume-type gp3 --watch

# Create with sc1 (cold storage) and a shorter watch timeout
zpcli zpool create --volume-type sc1 --watch --timeout 900

# You started create without --watch; reattach to the same job
zpcli zpool create --resume
```

---

## delete

```text
zpcli zpool delete <zpool_id> [--json]
```

Deletes the zpool with the given ID. Deletion is **permanent**; all data on the zpool is removed. Use `zpcli zpool list` to see zpool IDs.

**Argument**

- **zpool_id** — The zpool ID to delete (e.g. `law-hotel-shape-community`). Same format as other resource IDs; see [Resource IDs](../../../../docs/reference/ids.md).

**Options**

- `--json` — Output raw JSON. When used, the CLI **skips the confirmation prompt** and deletes immediately.

**Confirmation**

In non-JSON mode, the CLI asks for confirmation before deleting (e.g. “Are you sure you want to delete ZPool &lt;zpool_id&gt;?”). Answer yes to proceed.

**When the zpool is not found,** the CLI reports that the zpool was not found.

**Examples**

```text
zpcli zpool delete law-hotel-shape-community
zpcli zpool delete law-hotel-shape-community --json
```

---

## modify

```text
zpcli zpool modify <zpool_id> [OPTIONS]
```

Submits a **volume type** change for the zpool’s EBS volume(s): **gp3** ↔ **sc1**. The API accepts the request and returns a **job ID**; the actual modification runs asynchronously. Use `--watch` to have the CLI poll until the modification completes, or poll with job commands.

AWS enforces a **6-hour cooldown** between volume modifications. If you try to modify again before the cooldown expires, the CLI reports a conflict. Use `--wait-until-able` to have the CLI wait for the cooldown to expire and then submit the modification automatically.

> **Tip:** If you know you’ll hit the cooldown (e.g. you just modified and want to switch back), use `--wait-until-able` so the CLI waits and submits in one step instead of you retrying after 6 hours.

**Argument**

- **zpool_id** — The zpool to modify. Use `zpcli zpool list` to see IDs.

**Options**

- `--type <type>` — **Required** when not using `--resume`. Target EBS volume type. Choices:
  - **gp3** — General Purpose SSD. Use for higher performance; typically higher cost than sc1.
  - **sc1** — Cold HDD. Use for lower cost when access patterns are less demanding.
  You can switch between them (e.g. gp3 → sc1 to save cost, or sc1 → gp3 for better performance). Unsupported types (e.g. st1) are rejected; use gp3 or sc1 only.
- `--watch` — After submitting the modify job, poll until the modification completes (or timeout). Without `--watch`, the command prints a success message and the job ID; you can use job commands or `--resume` later to monitor.
- `--wait-until-able` — Before submitting, check whether the zpool’s volume(s) are in the AWS 6-hour cooldown. If any volume cannot be modified yet, the CLI **waits** until the cooldown expires (showing status and retry time), then submits the modification. There is no timeout for this wait (the end time is known); use Ctrl+C to abort if needed. Use this when you want to “modify as soon as allowed” in one command.
- `--resume` — Do not submit a new modification; find an existing **zpool modify** job for this zpool that is still in progress and monitor it until completion (or timeout). Requires no `--type`. Useful if you ran `modify` without `--watch` and want to reattach.
- `--timeout <seconds>` — Timeout in seconds when using `--watch` or `--resume`. Default: **1800** (30 minutes).
- `--json` — Output raw JSON instead of the formatted messages.
- `--local` — When showing cooldown retry time (e.g. after a conflict or during `--wait-until-able`), show timestamps in local timezone instead of UTC.

**When you omit `--type` and are not using `--resume`,** the CLI reports that `--type` is required.

**When you see a conflict:** Typically the volume is in the 6-hour cooldown or another modification is in progress. The CLI prints when you can retry (and a short explanation) when that information is available. Retry after that time, or use `--wait-until-able` next time to wait and submit in one go.

**Success output (without `--watch`)**

- Message that the modification was submitted.
- **Submitted:** X/Y volumes (how many were submitted vs discovered).

**Examples**

```text
# Submit gp3 → sc1 (e.g. to reduce cost); poll status yourself
zpcli zpool modify law-hotel-shape-community --type sc1

# Submit and watch until completion
zpcli zpool modify law-hotel-shape-community --type gp3 --watch

# Wait for cooldown to expire, then submit modification (no separate retry)
zpcli zpool modify law-hotel-shape-community --type sc1 --wait-until-able

# You ran modify without --watch; reattach to the same job
zpcli zpool modify law-hotel-shape-community --resume
```

---

## expand

```text
zpcli zpool expand <zpool_id> --size <n> [--json]
```

>**Not yet implemented.** This command will expand an existing zpool’s size (resize EBS volumes and expand the ZFS pool). Currently the CLI prints a short message that expansion is planned for a future release. The `--size` and `--json` options are accepted but have no effect.

**Argument**

- **zpool_id** — The zpool you would expand (ignored for now).

**Options**

- `--size <n>` — Intended: new size in GiB (ignored for now).
- `--json` — Output raw JSON (ignored for now).

**Examples**

```text
# Will fail with "not yet implemented" message
zpcli zpool expand law-hotel-shape-community --size 250
```

---

## scrub

```text
zpcli zpool scrub <zpool_id> [OPTIONS]
```

Starts a **ZFS scrub** on the zpool (a full check of data integrity). You get a **job ID** immediately; the scrub runs asynchronously. Use `--watch` to have the CLI poll until the scrub completes (or times out), or use job commands to check status.

**Argument**

- **zpool_id** — The zpool to scrub. Use `zpcli zpool list` to see IDs.

**Options**

- `--watch` — After starting the scrub job, poll until the job completes (succeeded or failed) or the timeout is reached. Without `--watch`, the command prints the job ID and exits.
- `--resume` — Do not start a new scrub; find an existing **zpool scrub** job for this zpool that is still in progress and monitor it until completion (or timeout). Useful if you ran `scrub` without `--watch` and want to reattach.
- `--timeout <seconds>` — Timeout in seconds when using `--watch` or `--resume`. Default: **1800** (30 minutes). Scrubs can take a long time on large pools; increase if needed.
- `--json` — Output raw JSON instead of the formatted messages.

**Success output (without `--watch`)**

- Message that scrub started for the zpool.
- **Job ID** — Use with `zpcli job get <job_id>` or `zpcli job history <job_id>`, or run `zpcli zpool scrub <zpool_id> --resume` to reattach.

**Examples**

```text
# Start scrub and get job ID
zpcli zpool scrub law-hotel-shape-community

# Start scrub and watch until completion (default 30 min timeout)
zpcli zpool scrub law-hotel-shape-community --watch

# Longer timeout for a large pool
zpcli zpool scrub law-hotel-shape-community --watch --timeout 3600

# Reattach to an existing scrub job
zpcli zpool scrub law-hotel-shape-community --resume
```

---

## See also

- [Command reference](commands.md)
- [Resource IDs](../../../../docs/reference/ids.md) — Zpool IDs and the four-word hyphenated format
- [Async jobs](../../../../docs/reference/async-jobs.md) — Job IDs, polling, `--watch`, timeouts
- [Storage units](../../../../docs/reference/storage-units.md) — GiB; size params and defaults
- [Job commands](commands-job.md) — List jobs, get job, job history (and `--watch`)
