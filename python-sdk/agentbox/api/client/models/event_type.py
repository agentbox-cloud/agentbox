from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.thresholds import Thresholds


T = TypeVar("T", bound="EventType")


@_attrs_define
class EventType:
    """
    Attributes:
        allow_threshold (bool): event allow threshold
        category (str): event category
        description (str): event description
        enabled (bool): event enabled
        event_type (str): event type
        msg_template (str): event msg template
        title (str): event title
        interval_seconds (Union[Unset, int]): event interval seconds
        max_per_day (Union[Unset, int]): event max per day
        max_per_interval (Union[Unset, int]): event max per interval
        threshold (Union[Unset, Thresholds]):
    """

    allow_threshold: bool
    category: str
    description: str
    enabled: bool
    event_type: str
    msg_template: str
    title: str
    interval_seconds: Union[Unset, int] = UNSET
    max_per_day: Union[Unset, int] = UNSET
    max_per_interval: Union[Unset, int] = UNSET
    threshold: Union[Unset, "Thresholds"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        allow_threshold = self.allow_threshold

        category = self.category

        description = self.description

        enabled = self.enabled

        event_type = self.event_type

        msg_template = self.msg_template

        title = self.title

        interval_seconds = self.interval_seconds

        max_per_day = self.max_per_day

        max_per_interval = self.max_per_interval

        threshold: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.threshold, Unset):
            threshold = self.threshold.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "allow_threshold": allow_threshold,
                "category": category,
                "description": description,
                "enabled": enabled,
                "event_type": event_type,
                "msg_template": msg_template,
                "title": title,
            }
        )
        if interval_seconds is not UNSET:
            field_dict["interval_seconds"] = interval_seconds
        if max_per_day is not UNSET:
            field_dict["max_per_day"] = max_per_day
        if max_per_interval is not UNSET:
            field_dict["max_per_interval"] = max_per_interval
        if threshold is not UNSET:
            field_dict["threshold"] = threshold

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.thresholds import Thresholds

        d = dict(src_dict)
        allow_threshold = d.pop("allow_threshold")

        category = d.pop("category")

        description = d.pop("description")

        enabled = d.pop("enabled")

        event_type = d.pop("event_type")

        msg_template = d.pop("msg_template")

        title = d.pop("title")

        interval_seconds = d.pop("interval_seconds", UNSET)

        max_per_day = d.pop("max_per_day", UNSET)

        max_per_interval = d.pop("max_per_interval", UNSET)

        _threshold = d.pop("threshold", UNSET)
        threshold: Union[Unset, Thresholds]
        if isinstance(_threshold, Unset):
            threshold = UNSET
        else:
            threshold = Thresholds.from_dict(_threshold)

        event_type = cls(
            allow_threshold=allow_threshold,
            category=category,
            description=description,
            enabled=enabled,
            event_type=event_type,
            msg_template=msg_template,
            title=title,
            interval_seconds=interval_seconds,
            max_per_day=max_per_day,
            max_per_interval=max_per_interval,
            threshold=threshold,
        )

        event_type.additional_properties = d
        return event_type

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
