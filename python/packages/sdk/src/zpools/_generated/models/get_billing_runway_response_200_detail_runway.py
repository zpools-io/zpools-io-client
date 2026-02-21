from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetBillingRunwayResponse200DetailRunway")


@_attrs_define
class GetBillingRunwayResponse200DetailRunway:
    """
    Attributes:
        daily_burn_ebs (float | Unset): Daily burn from EBS (current allocation)
        daily_burn_total (float | Unset):
        daily_tou_avg (float | Unset):
        days_remaining_adjusted (float | Unset): Runway including ToU over lookback
        days_remaining_ebs (float | Unset): Runway from EBS only
        ending_balance (float | Unset): Current account balance
        lookback_days (int | Unset):
        tou_total_in_lookback (float | Unset):
    """

    daily_burn_ebs: float | Unset = UNSET
    daily_burn_total: float | Unset = UNSET
    daily_tou_avg: float | Unset = UNSET
    days_remaining_adjusted: float | Unset = UNSET
    days_remaining_ebs: float | Unset = UNSET
    ending_balance: float | Unset = UNSET
    lookback_days: int | Unset = UNSET
    tou_total_in_lookback: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        daily_burn_ebs = self.daily_burn_ebs

        daily_burn_total = self.daily_burn_total

        daily_tou_avg = self.daily_tou_avg

        days_remaining_adjusted = self.days_remaining_adjusted

        days_remaining_ebs = self.days_remaining_ebs

        ending_balance = self.ending_balance

        lookback_days = self.lookback_days

        tou_total_in_lookback = self.tou_total_in_lookback

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if daily_burn_ebs is not UNSET:
            field_dict["daily_burn_ebs"] = daily_burn_ebs
        if daily_burn_total is not UNSET:
            field_dict["daily_burn_total"] = daily_burn_total
        if daily_tou_avg is not UNSET:
            field_dict["daily_tou_avg"] = daily_tou_avg
        if days_remaining_adjusted is not UNSET:
            field_dict["days_remaining_adjusted"] = days_remaining_adjusted
        if days_remaining_ebs is not UNSET:
            field_dict["days_remaining_ebs"] = days_remaining_ebs
        if ending_balance is not UNSET:
            field_dict["ending_balance"] = ending_balance
        if lookback_days is not UNSET:
            field_dict["lookback_days"] = lookback_days
        if tou_total_in_lookback is not UNSET:
            field_dict["tou_total_in_lookback"] = tou_total_in_lookback

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        daily_burn_ebs = d.pop("daily_burn_ebs", UNSET)

        daily_burn_total = d.pop("daily_burn_total", UNSET)

        daily_tou_avg = d.pop("daily_tou_avg", UNSET)

        days_remaining_adjusted = d.pop("days_remaining_adjusted", UNSET)

        days_remaining_ebs = d.pop("days_remaining_ebs", UNSET)

        ending_balance = d.pop("ending_balance", UNSET)

        lookback_days = d.pop("lookback_days", UNSET)

        tou_total_in_lookback = d.pop("tou_total_in_lookback", UNSET)

        get_billing_runway_response_200_detail_runway = cls(
            daily_burn_ebs=daily_burn_ebs,
            daily_burn_total=daily_burn_total,
            daily_tou_avg=daily_tou_avg,
            days_remaining_adjusted=days_remaining_adjusted,
            days_remaining_ebs=days_remaining_ebs,
            ending_balance=ending_balance,
            lookback_days=lookback_days,
            tou_total_in_lookback=tou_total_in_lookback,
        )

        get_billing_runway_response_200_detail_runway.additional_properties = d
        return get_billing_runway_response_200_detail_runway

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
