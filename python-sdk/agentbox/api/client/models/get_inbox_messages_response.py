from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inbox_message import InboxMessage


T = TypeVar("T", bound="GetInboxMessagesResponse")


@_attrs_define
class GetInboxMessagesResponse:
    """
    Attributes:
        messages (list['InboxMessage']):
        filter_total (Union[Unset, int]): filter_total
        page (Union[Unset, int]): page
        page_size (Union[Unset, int]): page_size
        read_count (Union[Unset, int]): read_count
        system_count (Union[Unset, int]): system_count
        team_count (Union[Unset, int]): team_count
        total (Union[Unset, int]): total
        unread_count (Union[Unset, int]): unread_count
    """

    messages: list["InboxMessage"]
    filter_total: Union[Unset, int] = UNSET
    page: Union[Unset, int] = UNSET
    page_size: Union[Unset, int] = UNSET
    read_count: Union[Unset, int] = UNSET
    system_count: Union[Unset, int] = UNSET
    team_count: Union[Unset, int] = UNSET
    total: Union[Unset, int] = UNSET
    unread_count: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        messages = []
        for messages_item_data in self.messages:
            messages_item = messages_item_data.to_dict()
            messages.append(messages_item)

        filter_total = self.filter_total

        page = self.page

        page_size = self.page_size

        read_count = self.read_count

        system_count = self.system_count

        team_count = self.team_count

        total = self.total

        unread_count = self.unread_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "messages": messages,
            }
        )
        if filter_total is not UNSET:
            field_dict["filter_total"] = filter_total
        if page is not UNSET:
            field_dict["page"] = page
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if read_count is not UNSET:
            field_dict["read_count"] = read_count
        if system_count is not UNSET:
            field_dict["system_count"] = system_count
        if team_count is not UNSET:
            field_dict["team_count"] = team_count
        if total is not UNSET:
            field_dict["total"] = total
        if unread_count is not UNSET:
            field_dict["unread_count"] = unread_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inbox_message import InboxMessage

        d = dict(src_dict)
        messages = []
        _messages = d.pop("messages")
        for messages_item_data in _messages:
            messages_item = InboxMessage.from_dict(messages_item_data)

            messages.append(messages_item)

        filter_total = d.pop("filter_total", UNSET)

        page = d.pop("page", UNSET)

        page_size = d.pop("page_size", UNSET)

        read_count = d.pop("read_count", UNSET)

        system_count = d.pop("system_count", UNSET)

        team_count = d.pop("team_count", UNSET)

        total = d.pop("total", UNSET)

        unread_count = d.pop("unread_count", UNSET)

        get_inbox_messages_response = cls(
            messages=messages,
            filter_total=filter_total,
            page=page,
            page_size=page_size,
            read_count=read_count,
            system_count=system_count,
            team_count=team_count,
            total=total,
            unread_count=unread_count,
        )

        get_inbox_messages_response.additional_properties = d
        return get_inbox_messages_response

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
