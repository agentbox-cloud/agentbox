from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CLILoginResponse")


@_attrs_define
class CLILoginResponse:
    """
    Attributes:
        access_token (str): Access token
        email (str): Email
        team_api_key (str): Team api key
        team_id (str): Team id
        team_name (str): Team name
    """

    access_token: str
    email: str
    team_api_key: str
    team_id: str
    team_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_token = self.access_token

        email = self.email

        team_api_key = self.team_api_key

        team_id = self.team_id

        team_name = self.team_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "access_token": access_token,
                "email": email,
                "team_api_key": team_api_key,
                "team_id": team_id,
                "team_name": team_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        access_token = d.pop("access_token")

        email = d.pop("email")

        team_api_key = d.pop("team_api_key")

        team_id = d.pop("team_id")

        team_name = d.pop("team_name")

        cli_login_response = cls(
            access_token=access_token,
            email=email,
            team_api_key=team_api_key,
            team_id=team_id,
            team_name=team_name,
        )

        cli_login_response.additional_properties = d
        return cli_login_response

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
