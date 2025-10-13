from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserTeamRequest")


@_attrs_define
class UserTeamRequest:
    """
    Attributes:
        email (str): Email name
        team_id (str): Identifier of the team
        is_default (Union[Unset, bool]): Whether the team is the default team
    """

    email: str
    team_id: str
    is_default: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        team_id = self.team_id

        is_default = self.is_default

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "teamID": team_id,
            }
        )
        if is_default is not UNSET:
            field_dict["isDefault"] = is_default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        team_id = d.pop("teamID")

        is_default = d.pop("isDefault", UNSET)

        user_team_request = cls(
            email=email,
            team_id=team_id,
            is_default=is_default,
        )

        user_team_request.additional_properties = d
        return user_team_request

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
