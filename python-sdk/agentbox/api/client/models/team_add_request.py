from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TeamAddRequest")


@_attrs_define
class TeamAddRequest:
    """
    Attributes:
        name (Union[Unset, str]): Name of the team
        profile_picture_url (Union[Unset, str]): URL of the profile picture for the team
        team_id (Union[Unset, str]): Identifier of the team
    """

    name: Union[Unset, str] = UNSET
    profile_picture_url: Union[Unset, str] = UNSET
    team_id: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        profile_picture_url = self.profile_picture_url

        team_id = self.team_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if profile_picture_url is not UNSET:
            field_dict["profile_picture_url"] = profile_picture_url
        if team_id is not UNSET:
            field_dict["teamID"] = team_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        profile_picture_url = d.pop("profile_picture_url", UNSET)

        team_id = d.pop("teamID", UNSET)

        team_add_request = cls(
            name=name,
            profile_picture_url=profile_picture_url,
            team_id=team_id,
        )

        team_add_request.additional_properties = d
        return team_add_request

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
