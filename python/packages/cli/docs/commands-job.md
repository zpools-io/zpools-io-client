# Job commands

`zpcli job` — List and inspect background jobs. Many zpool operations (create, modify, scrub) are asynchronous: the CLI returns a **job ID** immediately; you use these commands to check status and view the timeline. Job IDs use the standard [resource ID format](../../../../docs/reference/ids.md).

See [Async jobs](../../../../docs/reference/async-jobs.md) for how jobs relate to zpool commands and the `--watch` flag.

## Commands

- `zpcli job list` — List jobs with optional filtering and sorting.
- `zpcli job get <job_id>` — Show details for one job.
- `zpcli job history <job_id>` — Show status-change timeline; optionally watch until completion.

---

## Why jobs exist

Operations such as **zpool create** and **zpool scrub** can take minutes to hours. You get a **job ID** right away. The job moves through states (e.g. queued → in progress → succeeded or failed). Volume type changes from **zpool modify** are also asynchronous, but they are tracked through zpool volume state instead of job history. You can:

- **Poll once:** `zpcli job get <job_id>` or `zpcli job history <job_id>` to see current state and timeline.
- **Watch on the originating command:** Many zpool commands support `--watch` so the CLI polls until the job completes (or times out).
- **Watch history:** `zpcli job history <job_id> --watch` polls and updates the history display until the job completes or you hit a timeout.

---

## list

```text
zpcli job list [OPTIONS]
```

Lists background jobs for the authenticated user. Default is the 100 most recent jobs, newest first.

**Output columns**

- **ID** — Job ID (use with `job get` and `job history`).
- **Type** — Operation type (e.g. `zpool_create`, `zpool_scrub`, `zpool_modify`).
- **Status** — Current state (e.g. `succeeded`, `failed`, `in progress`, `queued`).
- **Age** — Time since the job was created (e.g. `-3d6h`, `-1h`, `-5m`).
- **Message** — Latest status message (truncated in the table).

**Options**

- `--limit`, `-n` — Maximum number of jobs to return (1–1000). Default: 100.
- `--before` — Only jobs created before this time (ISO 8601).
- `--after` — Only jobs created after this time (ISO 8601).
- `--sort` — `asc` (oldest first) or `desc` (newest first). Default: `desc`.
- `--json` — Output raw JSON instead of the table.

**Example**

```text
zpcli job list --limit 5
zpcli job list --sort asc --limit 20
```

---

## get

```text
zpcli job get <job_id> [OPTIONS]
```

Shows details for a single job: ID, type, status, created/updated timestamps, and if failed, the error message. Use this for a one-off check.

**Options**

- `--json` — Output raw JSON.
- `--local` — Show timestamps in local timezone instead of UTC.

**When the job is not found,** the CLI reports that the job was not found.

---

## history

```text
zpcli job history <job_id> [OPTIONS]
```

Shows the **status-change timeline** for a job: each event has a timestamp, status (e.g. queued, in progress, succeeded), and message. This is the main way to see what the job did step by step (e.g. “Locking zpool”, “Scrubbing zfs pool”, “completed successfully”).

**Output (default: one-shot)**

A table with:

- **Timestamp** — When the event occurred (UTC unless `--local`).
- **Age** — Relative time (e.g. `-3d6h`).
- **Status** — Event state (queued, in progress, succeeded, failed, etc.).
- **Message** — Description (e.g. “Job successfully added to the queue”, “Worker claimed job; starting execution”, “zpool_scrub job completed successfully (duration: 0m13s)”).

**Options**

- `--json` — Output raw JSON (one-shot only; cannot be combined with `--watch`).
- `--watch` — Keep polling and redrawing the history until the job reaches a terminal state (succeeded, failed, cancelled) or the timeout is reached. Requires an interactive terminal. Useful when you started a long-running job and want to watch it finish.
- `--timeout` — Maximum seconds to wait when using `--watch`. Default: 1800 (30 minutes).
- `--poll-interval` — Seconds between polls when using `--watch`. Default: 5.
- `--local` — Show timestamps in local timezone instead of UTC.

**Constraints**

- `--watch` and `--json` cannot be used together.
- `--watch` requires an interactive terminal (the CLI will report an error otherwise).

**Example**

```text
# One-shot: show current history
zpcli job history JOB_ID

# Watch until the job completes (interactive only)
zpcli job history JOB_ID --watch --timeout 600
```

---

## Relation to zpool commands

- **zpool create / modify / scrub** return a job ID. You can then run `zpcli job get <job_id>` or `zpcli job history <job_id>` to check status and timeline.
- Alternatively, use **`--watch`** on those commands so the CLI polls for completion (or timeout) and then shows the outcome.
- **job history --watch** is another way to “wait” for a job you already started: it polls and updates the history until the job finishes.

---

## See also

- [Command reference](commands.md)
- [Resource IDs](../../../../docs/reference/ids.md) — Job IDs and the four-word hyphenated format
- [Async jobs](../../../../docs/reference/async-jobs.md) — Polling, `--watch`, timeouts
- [Zpool commands](commands-zpool.md) — Commands that return job IDs and support `--watch`
