from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserUpdateRequest")


@_attrs_define
class UserUpdateRequest:
    """
    Attributes:
        email (Union[Unset, str]): Email name
        email_redirect_to (Union[Unset, str]): Url for the redirect to verify
        name (Union[Unset, str]): Name of the user
        password (Union[Unset, str]): Password of user account
    """

    email: Union[Unset, str] = UNSET
    email_redirect_to: Union[Unset, str] = UNSET
    name: Union[Unset, str] = UNSET
    password: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        email_redirect_to = self.email_redirect_to

        name = self.name

        password = self.password

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if email is not UNSET:
            field_dict["email"] = email
        if email_redirect_to is not UNSET:
            field_dict["emailRedirectTo"] = email_redirect_to
        if name is not UNSET:
            field_dict["name"] = name
        if password is not UNSET:
            field_dict["password"] = password

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email", UNSET)

        email_redirect_to = d.pop("emailRedirectTo", UNSET)

        name = d.pop("name", UNSET)

        password = d.pop("password", UNSET)

        user_update_request = cls(
            email=email,
            email_redirect_to=email_redirect_to,
            name=name,
            password=password,
        )

        user_update_request.additional_properties = d
        return user_update_request

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
