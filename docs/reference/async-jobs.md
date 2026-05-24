# Async jobs

Many zpools.io operations are **asynchronous**: the API accepts the request immediately and completion is tracked by polling status. Some operations return a **job ID**; EBS volume modifications are tracked through zpool volume state.

## Operations that return job IDs

Examples:

- Create zpool
- Modify zpool (volume type changes are tracked through zpool volume state)
- Scrub zpool

The exact list is in the [API spec](../../spec/README.md) and in the [CLI command reference](../../python/packages/cli/docs/commands.md) and [SDK API reference](../../python/packages/sdk/docs/api-reference.md).

## Job states

Jobs move through states such as pending, running, completed, failed. The API and clients expose the current state (e.g. `state` or `status`) so you can poll until completion or failure.

## Polling and timeouts

- **CLI:** Use the `--watch` flag on supported commands to poll until the operation completes (or a timeout is reached). Without `--watch`, commands that return job IDs can be checked with job commands (e.g. `zpcli job get <job_id>`); zpool volume modifications can be checked with `zpcli zpool list` or watched with `zpcli zpool modify <zpool_id> --resume`. See [CLI command reference](../../python/packages/cli/docs/commands.md).
- **SDK:** Use the client’s job methods (e.g. `get_job`) to poll, or use provided helpers (e.g. `JobPoller`) if documented in the SDK. See [SDK API reference](../../python/packages/sdk/docs/api-reference.md).

If the operation takes longer than your watch timeout, the client exits with watch-timeout status **3**; the underlying operation continues on the server. You can still query job status by job ID where available, or inspect zpool volume state for EBS modifications.

## See also

- [Troubleshooting](../troubleshooting.md) — Job timeouts.
- CLI: [commands](../../python/packages/cli/docs/commands.md) (async vs sync, `--watch`).
- SDK: [API reference](../../python/packages/sdk/docs/api-reference.md) (jobs, polling helpers).
