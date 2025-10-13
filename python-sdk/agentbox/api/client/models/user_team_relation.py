from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserTeamRelation")


@_attrs_define
class UserTeamRelation:
    """
    Attributes:
        team_id (str): Identifier of the team
        user_id (str): User id
        is_default (Union[Unset, bool]): Whether the team is the default team
    """

    team_id: str
    user_id: str
    is_default: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        team_id = self.team_id

        user_id = self.user_id

        is_default = self.is_default

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "teamID": team_id,
                "userID": user_id,
            }
        )
        if is_default is not UNSET:
            field_dict["isDefault"] = is_default

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        team_id = d.pop("teamID")

        user_id = d.pop("userID")

        is_default = d.pop("isDefault", UNSET)

        user_team_relation = cls(
            team_id=team_id,
            user_id=user_id,
            is_default=is_default,
        )

        user_team_relation.additional_properties = d
        return user_team_relation

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
