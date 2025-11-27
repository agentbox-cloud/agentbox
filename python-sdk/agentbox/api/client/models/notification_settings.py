from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.event_type import EventType
    from ..models.recipients import Recipients


T = TypeVar("T", bound="NotificationSettings")


@_attrs_define
class NotificationSettings:
    """
    Attributes:
        events (list['EventType']):
        channels (Union[Unset, list[str]]): channels
        is_owner (Union[Unset, bool]): is_owner
        recipients (Union[Unset, Recipients]):
        team_id (Union[Unset, str]): team_id
    """

    events: list["EventType"]
    channels: Union[Unset, list[str]] = UNSET
    is_owner: Union[Unset, bool] = UNSET
    recipients: Union[Unset, "Recipients"] = UNSET
    team_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        events = []
        for events_item_data in self.events:
            events_item = events_item_data.to_dict()
            events.append(events_item)

        channels: Union[Unset, list[str]] = UNSET
        if not isinstance(self.channels, Unset):
            channels = self.channels

        is_owner = self.is_owner

        recipients: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.recipients, Unset):
            recipients = self.recipients.to_dict()

        team_id = self.team_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "events": events,
            }
        )
        if channels is not UNSET:
            field_dict["channels"] = channels
        if is_owner is not UNSET:
            field_dict["is_owner"] = is_owner
        if recipients is not UNSET:
            field_dict["recipients"] = recipients
        if team_id is not UNSET:
            field_dict["team_id"] = team_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.event_type import EventType
        from ..models.recipients import Recipients

        d = dict(src_dict)
        events = []
        _events = d.pop("events")
        for events_item_data in _events:
            events_item = EventType.from_dict(events_item_data)

            events.append(events_item)

        channels = cast(list[str], d.pop("channels", UNSET))

        is_owner = d.pop("is_owner", UNSET)

        _recipients = d.pop("recipients", UNSET)
        recipients: Union[Unset, Recipients]
        if isinstance(_recipients, Unset):
            recipients = UNSET
        else:
            recipients = Recipients.from_dict(_recipients)

        team_id = d.pop("team_id", UNSET)

        notification_settings = cls(
            events=events,
            channels=channels,
            is_owner=is_owner,
            recipients=recipients,
            team_id=team_id,
        )

        notification_settings.additional_properties = d
        return notification_settings

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
