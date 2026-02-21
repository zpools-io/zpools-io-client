import datetime
from http import HTTPStatus
from typing import Any, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...models.get_billing_summary_response_200 import GetBillingSummaryResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    since: datetime.date | Unset = UNSET,
    until: datetime.date | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_since: str | Unset = UNSET
    if not isinstance(since, Unset):
        json_since = since.isoformat()
    params["since"] = json_since

    json_until: str | Unset = UNSET
    if not isinstance(until, Unset):
        json_until = until.isoformat()
    params["until"] = json_until

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/billing/summary",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | GetBillingSummaryResponse200:
    if response.status_code == 200:
        response_200 = GetBillingSummaryResponse200.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    response_default = cast(Any, None)
    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | GetBillingSummaryResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    since: datetime.date | Unset = UNSET,
    until: datetime.date | Unset = UNSET,
) -> Response[Any | GetBillingSummaryResponse200]:
    """Get billing summary

     Retrieve aggregated billing summary for a date range (max 32 days). When since/until omitted,
    returns the preceding calendar month. Groups hourly storage charges into periods, includes
    time_of_use_summary (by source, non-zero charges, zero egress count), and calculates totals. For
    longer ranges use the ledger API.

    Args:
        since (datetime.date | Unset):
        until (datetime.date | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | GetBillingSummaryResponse200]
    """

    kwargs = _get_kwargs(
        since=since,
        until=until,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    since: datetime.date | Unset = UNSET,
    until: datetime.date | Unset = UNSET,
) -> Any | GetBillingSummaryResponse200 | None:
    """Get billing summary

     Retrieve aggregated billing summary for a date range (max 32 days). When since/until omitted,
    returns the preceding calendar month. Groups hourly storage charges into periods, includes
    time_of_use_summary (by source, non-zero charges, zero egress count), and calculates totals. For
    longer ranges use the ledger API.

    Args:
        since (datetime.date | Unset):
        until (datetime.date | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | GetBillingSummaryResponse200
    """

    return sync_detailed(
        client=client,
        since=since,
        until=until,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    since: datetime.date | Unset = UNSET,
    until: datetime.date | Unset = UNSET,
) -> Response[Any | GetBillingSummaryResponse200]:
    """Get billing summary

     Retrieve aggregated billing summary for a date range (max 32 days). When since/until omitted,
    returns the preceding calendar month. Groups hourly storage charges into periods, includes
    time_of_use_summary (by source, non-zero charges, zero egress count), and calculates totals. For
    longer ranges use the ledger API.

    Args:
        since (datetime.date | Unset):
        until (datetime.date | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | GetBillingSummaryResponse200]
    """

    kwargs = _get_kwargs(
        since=since,
        until=until,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    since: datetime.date | Unset = UNSET,
    until: datetime.date | Unset = UNSET,
) -> Any | GetBillingSummaryResponse200 | None:
    """Get billing summary

     Retrieve aggregated billing summary for a date range (max 32 days). When since/until omitted,
    returns the preceding calendar month. Groups hourly storage charges into periods, includes
    time_of_use_summary (by source, non-zero charges, zero egress count), and calculates totals. For
    longer ranges use the ledger API.

    Args:
        since (datetime.date | Unset):
        until (datetime.date | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | GetBillingSummaryResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            since=since,
            until=until,
        )
    ).parsed
