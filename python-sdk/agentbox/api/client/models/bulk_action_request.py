from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.bulk_action_request_action import BulkActionRequestAction

T = TypeVar("T", bound="BulkActionRequest")


@_attrs_define
class BulkActionRequest:
    """
    Attributes:
        action (BulkActionRequestAction): Action
        message_ids (list[str]):
    """

    action: BulkActionRequestAction
    message_ids: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        action = self.action.value

        message_ids = self.message_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action": action,
                "message_ids": message_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        action = BulkActionRequestAction(d.pop("action"))

        message_ids = cast(list[str], d.pop("message_ids"))

        bulk_action_request = cls(
            action=action,
            message_ids=message_ids,
        )

        bulk_action_request.additional_properties = d
        return bulk_action_request

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
