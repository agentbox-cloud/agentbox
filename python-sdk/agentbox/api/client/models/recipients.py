from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="Recipients")


@_attrs_define
class Recipients:
    """
    Attributes:
        emails (list[str]): emails of custom contacts
        include_team (bool): include team members
        phones (list[str]): phones of custom contacts
    """

    emails: list[str]
    include_team: bool
    phones: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        emails = self.emails

        include_team = self.include_team

        phones = self.phones

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "emails": emails,
                "include_team": include_team,
                "phones": phones,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        emails = cast(list[str], d.pop("emails"))

        include_team = d.pop("include_team")

        phones = cast(list[str], d.pop("phones"))

        recipients = cls(
            emails=emails,
            include_team=include_team,
            phones=phones,
        )

        recipients.additional_properties = d
        return recipients

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
