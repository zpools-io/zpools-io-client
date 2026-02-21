from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="GetBillingSummaryResponse200DetailSummaryTimeOfUseSummaryBySourceAdditionalProperty")


@_attrs_define
class GetBillingSummaryResponse200DetailSummaryTimeOfUseSummaryBySourceAdditionalProperty:
    """
    Attributes:
        count (int | Unset):
        total_usd (float | Unset):
        zero_count (int | Unset):
    """

    count: int | Unset = UNSET
    total_usd: float | Unset = UNSET
    zero_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        total_usd = self.total_usd

        zero_count = self.zero_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if count is not UNSET:
            field_dict["count"] = count
        if total_usd is not UNSET:
            field_dict["total_usd"] = total_usd
        if zero_count is not UNSET:
            field_dict["zero_count"] = zero_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        count = d.pop("count", UNSET)

        total_usd = d.pop("total_usd", UNSET)

        zero_count = d.pop("zero_count", UNSET)

        get_billing_summary_response_200_detail_summary_time_of_use_summary_by_source_additional_property = cls(
            count=count,
            total_usd=total_usd,
            zero_count=zero_count,
        )

        get_billing_summary_response_200_detail_summary_time_of_use_summary_by_source_additional_property.additional_properties = d
        return get_billing_summary_response_200_detail_summary_time_of_use_summary_by_source_additional_property

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
