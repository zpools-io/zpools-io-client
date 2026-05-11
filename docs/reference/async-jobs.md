# Async jobs

Many zpools.io operations are **asynchronous**: the API accepts the request and returns a **job ID** immediately. Completion is tracked by polling job status.

## Operations that return job IDs

Examples:

- Create zpool
- Modify zpool (e.g. size, volume type)
- Scrub zpool

The exact list is in the [API spec](../../spec/README.md) and in the [CLI command reference](../../python/packages/cli/docs/commands.md) and [SDK API reference](../../python/packages/sdk/docs/api-reference.md).

## Job states

Jobs move through states such as pending, running, completed, failed. The API and clients expose the current state (e.g. `state` or `status`) so you can poll until completion or failure.

## Polling and timeouts

- **CLI:** Use the `--watch` flag on supported commands to poll until the job completes (or a timeout is reached). Without `--watch`, the command returns the job ID and you can check status with the job commands (e.g. `zpcli job get <job_id>`). See [CLI command reference](../../python/packages/cli/docs/commands.md).
- **SDK:** Use the client’s job methods (e.g. `get_job`) to poll, or use provided helpers (e.g. `JobPoller`) if documented in the SDK. See [SDK API reference](../../python/packages/sdk/docs/api-reference.md).

If the operation takes longer than your watch timeout, the client may exit with a timeout; the job continues on the server. You can still query job status by job ID.

## See also

- [Troubleshooting](../troubleshooting.md) — Job timeouts.
- CLI: [commands](../../python/packages/cli/docs/commands.md) (async vs sync, `--watch`).
- SDK: [API reference](../../python/packages/sdk/docs/api-reference.md) (jobs, polling helpers).
