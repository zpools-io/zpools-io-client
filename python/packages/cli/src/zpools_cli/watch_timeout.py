import json
from typing import Optional

import typer


WATCH_TIMEOUT_EXIT_CODE = 3


def exit_watch_timeout(
    console,
    *,
    message: str,
    json_output: bool = False,
    job_id: Optional[str] = None,
    zpool_id: Optional[str] = None,
    resume_command: Optional[str] = None,
    request_submitted: Optional[bool] = None,
) -> None:
    if json_output:
        payload = {
            "error": "watch_timeout",
            "message": message,
        }
        if job_id:
            payload["job_id"] = job_id
        if zpool_id:
            payload["zpool_id"] = zpool_id
        if resume_command:
            payload["resume_command"] = resume_command
        if request_submitted is not None:
            payload["request_submitted"] = request_submitted
        print(json.dumps(payload, indent=2))
    else:
        console.print(f"[yellow]Watch timed out:[/yellow] {message}")
        if job_id:
            console.print(f"Job ID: {job_id}")
        if resume_command:
            console.print(f"Resume watching: {resume_command}")

    raise typer.Exit(WATCH_TIMEOUT_EXIT_CODE)
