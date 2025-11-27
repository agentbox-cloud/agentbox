from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="InboxMessage")


@_attrs_define
class InboxMessage:
    """
    Attributes:
        content (str): content
        created_at (str): created_at
        event_type (str): event_type
        id (str): id
        is_read (bool): is_read
        message_level (str): message_level
        message_type (str): message_type
        priority (int): priority
        team_id (str): team_id
        title (str): title
        updated_at (str): updated_at
        user_id (str): user_id
    """

    content: str
    created_at: str
    event_type: str
    id: str
    is_read: bool
    message_level: str
    message_type: str
    priority: int
    team_id: str
    title: str
    updated_at: str
    user_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        content = self.content

        created_at = self.created_at

        event_type = self.event_type

        id = self.id

        is_read = self.is_read

        message_level = self.message_level

        message_type = self.message_type

        priority = self.priority

        team_id = self.team_id

        title = self.title

        updated_at = self.updated_at

        user_id = self.user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "content": content,
                "created_at": created_at,
                "event_type": event_type,
                "id": id,
                "is_read": is_read,
                "message_level": message_level,
                "message_type": message_type,
                "priority": priority,
                "team_id": team_id,
                "title": title,
                "updated_at": updated_at,
                "user_id": user_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        content = d.pop("content")

        created_at = d.pop("created_at")

        event_type = d.pop("event_type")

        id = d.pop("id")

        is_read = d.pop("is_read")

        message_level = d.pop("message_level")

        message_type = d.pop("message_type")

        priority = d.pop("priority")

        team_id = d.pop("team_id")

        title = d.pop("title")

        updated_at = d.pop("updated_at")

        user_id = d.pop("user_id")

        inbox_message = cls(
            content=content,
            created_at=created_at,
            event_type=event_type,
            id=id,
            is_read=is_read,
            message_level=message_level,
            message_type=message_type,
            priority=priority,
            team_id=team_id,
            title=title,
            updated_at=updated_at,
            user_id=user_id,
        )

        inbox_message.additional_properties = d
        return inbox_message

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
