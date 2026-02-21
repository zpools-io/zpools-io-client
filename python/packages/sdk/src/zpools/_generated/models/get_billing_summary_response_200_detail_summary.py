from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_billing_summary_response_200_detail_summary_credits_item import (
        GetBillingSummaryResponse200DetailSummaryCreditsItem,
    )
    from ..models.get_billing_summary_response_200_detail_summary_period import (
        GetBillingSummaryResponse200DetailSummaryPeriod,
    )
    from ..models.get_billing_summary_response_200_detail_summary_storage_charges_item import (
        GetBillingSummaryResponse200DetailSummaryStorageChargesItem,
    )
    from ..models.get_billing_summary_response_200_detail_summary_time_of_use_summary import (
        GetBillingSummaryResponse200DetailSummaryTimeOfUseSummary,
    )
    from ..models.get_billing_summary_response_200_detail_summary_totals import (
        GetBillingSummaryResponse200DetailSummaryTotals,
    )


T = TypeVar("T", bound="GetBillingSummaryResponse200DetailSummary")


@_attrs_define
class GetBillingSummaryResponse200DetailSummary:
    """
    Attributes:
        credits_ (list[GetBillingSummaryResponse200DetailSummaryCreditsItem] | Unset):
        period (GetBillingSummaryResponse200DetailSummaryPeriod | Unset):
        storage_charges (list[GetBillingSummaryResponse200DetailSummaryStorageChargesItem] | Unset):
        time_of_use_summary (GetBillingSummaryResponse200DetailSummaryTimeOfUseSummary | Unset): Time-of-use summary
            only (use ledger endpoint for per-entry detail)
        totals (GetBillingSummaryResponse200DetailSummaryTotals | Unset):
    """

    credits_: list[GetBillingSummaryResponse200DetailSummaryCreditsItem] | Unset = UNSET
    period: GetBillingSummaryResponse200DetailSummaryPeriod | Unset = UNSET
    storage_charges: list[GetBillingSummaryResponse200DetailSummaryStorageChargesItem] | Unset = UNSET
    time_of_use_summary: GetBillingSummaryResponse200DetailSummaryTimeOfUseSummary | Unset = UNSET
    totals: GetBillingSummaryResponse200DetailSummaryTotals | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        credits_: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.credits_, Unset):
            credits_ = []
            for credits_item_data in self.credits_:
                credits_item = credits_item_data.to_dict()
                credits_.append(credits_item)

        period: dict[str, Any] | Unset = UNSET
        if not isinstance(self.period, Unset):
            period = self.period.to_dict()

        storage_charges: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.storage_charges, Unset):
            storage_charges = []
            for storage_charges_item_data in self.storage_charges:
                storage_charges_item = storage_charges_item_data.to_dict()
                storage_charges.append(storage_charges_item)

        time_of_use_summary: dict[str, Any] | Unset = UNSET
        if not isinstance(self.time_of_use_summary, Unset):
            time_of_use_summary = self.time_of_use_summary.to_dict()

        totals: dict[str, Any] | Unset = UNSET
        if not isinstance(self.totals, Unset):
            totals = self.totals.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if credits_ is not UNSET:
            field_dict["credits"] = credits_
        if period is not UNSET:
            field_dict["period"] = period
        if storage_charges is not UNSET:
            field_dict["storage_charges"] = storage_charges
        if time_of_use_summary is not UNSET:
            field_dict["time_of_use_summary"] = time_of_use_summary
        if totals is not UNSET:
            field_dict["totals"] = totals

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_billing_summary_response_200_detail_summary_credits_item import (
            GetBillingSummaryResponse200DetailSummaryCreditsItem,
        )
        from ..models.get_billing_summary_response_200_detail_summary_period import (
            GetBillingSummaryResponse200DetailSummaryPeriod,
        )
        from ..models.get_billing_summary_response_200_detail_summary_storage_charges_item import (
            GetBillingSummaryResponse200DetailSummaryStorageChargesItem,
        )
        from ..models.get_billing_summary_response_200_detail_summary_time_of_use_summary import (
            GetBillingSummaryResponse200DetailSummaryTimeOfUseSummary,
        )
        from ..models.get_billing_summary_response_200_detail_summary_totals import (
            GetBillingSummaryResponse200DetailSummaryTotals,
        )

        d = dict(src_dict)
        _credits_ = d.pop("credits", UNSET)
        credits_: list[GetBillingSummaryResponse200DetailSummaryCreditsItem] | Unset = UNSET
        if _credits_ is not UNSET:
            credits_ = []
            for credits_item_data in _credits_:
                credits_item = GetBillingSummaryResponse200DetailSummaryCreditsItem.from_dict(credits_item_data)

                credits_.append(credits_item)

        _period = d.pop("period", UNSET)
        period: GetBillingSummaryResponse200DetailSummaryPeriod | Unset
        if isinstance(_period, Unset):
            period = UNSET
        else:
            period = GetBillingSummaryResponse200DetailSummaryPeriod.from_dict(_period)

        _storage_charges = d.pop("storage_charges", UNSET)
        storage_charges: list[GetBillingSummaryResponse200DetailSummaryStorageChargesItem] | Unset = UNSET
        if _storage_charges is not UNSET:
            storage_charges = []
            for storage_charges_item_data in _storage_charges:
                storage_charges_item = GetBillingSummaryResponse200DetailSummaryStorageChargesItem.from_dict(
                    storage_charges_item_data
                )

                storage_charges.append(storage_charges_item)

        _time_of_use_summary = d.pop("time_of_use_summary", UNSET)
        time_of_use_summary: GetBillingSummaryResponse200DetailSummaryTimeOfUseSummary | Unset
        if isinstance(_time_of_use_summary, Unset):
            time_of_use_summary = UNSET
        else:
            time_of_use_summary = GetBillingSummaryResponse200DetailSummaryTimeOfUseSummary.from_dict(
                _time_of_use_summary
            )

        _totals = d.pop("totals", UNSET)
        totals: GetBillingSummaryResponse200DetailSummaryTotals | Unset
        if isinstance(_totals, Unset):
            totals = UNSET
        else:
            totals = GetBillingSummaryResponse200DetailSummaryTotals.from_dict(_totals)

        get_billing_summary_response_200_detail_summary = cls(
            credits_=credits_,
            period=period,
            storage_charges=storage_charges,
            time_of_use_summary=time_of_use_summary,
            totals=totals,
        )

        get_billing_summary_response_200_detail_summary.additional_properties = d
        return get_billing_summary_response_200_detail_summary

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
