from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_billing_summary_response_200_detail_summary_time_of_use_summary_by_source import (
        GetBillingSummaryResponse200DetailSummaryTimeOfUseSummaryBySource,
    )


T = TypeVar("T", bound="GetBillingSummaryResponse200DetailSummaryTimeOfUseSummary")


@_attrs_define
class GetBillingSummaryResponse200DetailSummaryTimeOfUseSummary:
    """Time-of-use summary only (use ledger endpoint for per-entry detail)

    Attributes:
        by_source (GetBillingSummaryResponse200DetailSummaryTimeOfUseSummaryBySource | Unset):
        zero_egress_count (int | Unset):
    """

    by_source: GetBillingSummaryResponse200DetailSummaryTimeOfUseSummaryBySource | Unset = UNSET
    zero_egress_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        by_source: dict[str, Any] | Unset = UNSET
        if not isinstance(self.by_source, Unset):
            by_source = self.by_source.to_dict()

        zero_egress_count = self.zero_egress_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if by_source is not UNSET:
            field_dict["by_source"] = by_source
        if zero_egress_count is not UNSET:
            field_dict["zero_egress_count"] = zero_egress_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_billing_summary_response_200_detail_summary_time_of_use_summary_by_source import (
            GetBillingSummaryResponse200DetailSummaryTimeOfUseSummaryBySource,
        )

        d = dict(src_dict)
        _by_source = d.pop("by_source", UNSET)
        by_source: GetBillingSummaryResponse200DetailSummaryTimeOfUseSummaryBySource | Unset
        if isinstance(_by_source, Unset):
            by_source = UNSET
        else:
            by_source = GetBillingSummaryResponse200DetailSummaryTimeOfUseSummaryBySource.from_dict(_by_source)

        zero_egress_count = d.pop("zero_egress_count", UNSET)

        get_billing_summary_response_200_detail_summary_time_of_use_summary = cls(
            by_source=by_source,
            zero_egress_count=zero_egress_count,
        )

        get_billing_summary_response_200_detail_summary_time_of_use_summary.additional_properties = d
        return get_billing_summary_response_200_detail_summary_time_of_use_summary

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
