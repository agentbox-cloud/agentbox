from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.event_rule import EventRule


T = TypeVar("T", bound="Thresholds")


@_attrs_define
class Thresholds:
    """
    Attributes:
        interval_sec (Union[Unset, int]): interval sec
        max_per_day (Union[Unset, int]): max per day
        max_per_interval (Union[Unset, int]): max per interval
        rules (Union[Unset, list['EventRule']]):
    """

    interval_sec: Union[Unset, int] = UNSET
    max_per_day: Union[Unset, int] = UNSET
    max_per_interval: Union[Unset, int] = UNSET
    rules: Union[Unset, list["EventRule"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        interval_sec = self.interval_sec

        max_per_day = self.max_per_day

        max_per_interval = self.max_per_interval

        rules: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.rules, Unset):
            rules = []
            for rules_item_data in self.rules:
                rules_item = rules_item_data.to_dict()
                rules.append(rules_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if interval_sec is not UNSET:
            field_dict["interval_sec"] = interval_sec
        if max_per_day is not UNSET:
            field_dict["max_per_day"] = max_per_day
        if max_per_interval is not UNSET:
            field_dict["max_per_interval"] = max_per_interval
        if rules is not UNSET:
            field_dict["rules"] = rules

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.event_rule import EventRule

        d = dict(src_dict)
        interval_sec = d.pop("interval_sec", UNSET)

        max_per_day = d.pop("max_per_day", UNSET)

        max_per_interval = d.pop("max_per_interval", UNSET)

        rules = []
        _rules = d.pop("rules", UNSET)
        for rules_item_data in _rules or []:
            rules_item = EventRule.from_dict(rules_item_data)

            rules.append(rules_item)

        thresholds = cls(
            interval_sec=interval_sec,
            max_per_day=max_per_day,
            max_per_interval=max_per_interval,
            rules=rules,
        )

        thresholds.additional_properties = d
        return thresholds

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
