from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_billing_runway_response_200_detail_runway import GetBillingRunwayResponse200DetailRunway


T = TypeVar("T", bound="GetBillingRunwayResponse200Detail")


@_attrs_define
class GetBillingRunwayResponse200Detail:
    """
    Attributes:
        runway (GetBillingRunwayResponse200DetailRunway | Unset):
    """

    runway: GetBillingRunwayResponse200DetailRunway | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        runway: dict[str, Any] | Unset = UNSET
        if not isinstance(self.runway, Unset):
            runway = self.runway.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if runway is not UNSET:
            field_dict["runway"] = runway

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_billing_runway_response_200_detail_runway import GetBillingRunwayResponse200DetailRunway

        d = dict(src_dict)
        _runway = d.pop("runway", UNSET)
        runway: GetBillingRunwayResponse200DetailRunway | Unset
        if isinstance(_runway, Unset):
            runway = UNSET
        else:
            runway = GetBillingRunwayResponse200DetailRunway.from_dict(_runway)

        get_billing_runway_response_200_detail = cls(
            runway=runway,
        )

        get_billing_runway_response_200_detail.additional_properties = d
        return get_billing_runway_response_200_detail

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
