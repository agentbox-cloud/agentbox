from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="OauthCallbackParams")


@_attrs_define
class OauthCallbackParams:
    """
    Attributes:
        code (str): google / github code
        provider (str): google / github
        return_to (str): redirect url
    """

    code: str
    provider: str
    return_to: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        provider = self.provider

        return_to = self.return_to

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code": code,
                "provider": provider,
                "returnTo": return_to,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        code = d.pop("code")

        provider = d.pop("provider")

        return_to = d.pop("returnTo")

        oauth_callback_params = cls(
            code=code,
            provider=provider,
            return_to=return_to,
        )

        oauth_callback_params.additional_properties = d
        return oauth_callback_params

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
