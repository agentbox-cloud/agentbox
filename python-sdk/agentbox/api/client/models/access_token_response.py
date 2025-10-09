from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.access_token_response_user import AccessTokenResponseUser
    from ..models.access_token_response_weak_password import AccessTokenResponseWeakPassword


T = TypeVar("T", bound="AccessTokenResponse")


@_attrs_define
class AccessTokenResponse:
    """
    Attributes:
        access_token (str): Access token
        expires_at (int): Expires_at
        expires_in (int): Ixpires in
        provider_refresh_token (str): Provider refresh token
        provider_token (str): Provider token
        refresh_token (str): Refresh token
        token_type (str): Token type
        user (AccessTokenResponseUser): User
        weak_password (AccessTokenResponseWeakPassword): Weak password
    """

    access_token: str
    expires_at: int
    expires_in: int
    provider_refresh_token: str
    provider_token: str
    refresh_token: str
    token_type: str
    user: "AccessTokenResponseUser"
    weak_password: "AccessTokenResponseWeakPassword"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_token = self.access_token

        expires_at = self.expires_at

        expires_in = self.expires_in

        provider_refresh_token = self.provider_refresh_token

        provider_token = self.provider_token

        refresh_token = self.refresh_token

        token_type = self.token_type

        user = self.user.to_dict()

        weak_password = self.weak_password.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "access_token": access_token,
                "expires_at": expires_at,
                "expires_in": expires_in,
                "provider_refresh_token": provider_refresh_token,
                "provider_token": provider_token,
                "refresh_token": refresh_token,
                "token_type": token_type,
                "user": user,
                "weak_password": weak_password,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.access_token_response_user import AccessTokenResponseUser
        from ..models.access_token_response_weak_password import AccessTokenResponseWeakPassword

        d = dict(src_dict)
        access_token = d.pop("access_token")

        expires_at = d.pop("expires_at")

        expires_in = d.pop("expires_in")

        provider_refresh_token = d.pop("provider_refresh_token")

        provider_token = d.pop("provider_token")

        refresh_token = d.pop("refresh_token")

        token_type = d.pop("token_type")

        user = AccessTokenResponseUser.from_dict(d.pop("user"))

        weak_password = AccessTokenResponseWeakPassword.from_dict(d.pop("weak_password"))

        access_token_response = cls(
            access_token=access_token,
            expires_at=expires_at,
            expires_in=expires_in,
            provider_refresh_token=provider_refresh_token,
            provider_token=provider_token,
            refresh_token=refresh_token,
            token_type=token_type,
            user=user,
            weak_password=weak_password,
        )

        access_token_response.additional_properties = d
        return access_token_response

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
