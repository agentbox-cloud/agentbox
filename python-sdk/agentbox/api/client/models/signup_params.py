from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.signup_params_data import SignupParamsData


T = TypeVar("T", bound="SignupParams")


@_attrs_define
class SignupParams:
    """
    Attributes:
        email (str): email of the user
        password (str): Password of the user
        aud (Union[Unset, str]): aud
        channel (Union[Unset, str]): channel
        code_challenge (Union[Unset, str]): code_challenge
        code_challenge_method (Union[Unset, str]): code_challenge_method
        data (Union[Unset, SignupParamsData]): Map of data
        phone (Union[Unset, str]): phone of the user
        provider (Union[Unset, str]): provider
    """

    email: str
    password: str
    aud: Union[Unset, str] = UNSET
    channel: Union[Unset, str] = UNSET
    code_challenge: Union[Unset, str] = UNSET
    code_challenge_method: Union[Unset, str] = UNSET
    data: Union[Unset, "SignupParamsData"] = UNSET
    phone: Union[Unset, str] = UNSET
    provider: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        password = self.password

        aud = self.aud

        channel = self.channel

        code_challenge = self.code_challenge

        code_challenge_method = self.code_challenge_method

        data: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.data, Unset):
            data = self.data.to_dict()

        phone = self.phone

        provider = self.provider

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "password": password,
            }
        )
        if aud is not UNSET:
            field_dict["aud"] = aud
        if channel is not UNSET:
            field_dict["channel"] = channel
        if code_challenge is not UNSET:
            field_dict["code_challenge"] = code_challenge
        if code_challenge_method is not UNSET:
            field_dict["code_challenge_method"] = code_challenge_method
        if data is not UNSET:
            field_dict["data"] = data
        if phone is not UNSET:
            field_dict["phone"] = phone
        if provider is not UNSET:
            field_dict["provider"] = provider

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.signup_params_data import SignupParamsData

        d = dict(src_dict)
        email = d.pop("email")

        password = d.pop("password")

        aud = d.pop("aud", UNSET)

        channel = d.pop("channel", UNSET)

        code_challenge = d.pop("code_challenge", UNSET)

        code_challenge_method = d.pop("code_challenge_method", UNSET)

        _data = d.pop("data", UNSET)
        data: Union[Unset, SignupParamsData]
        if isinstance(_data, Unset):
            data = UNSET
        else:
            data = SignupParamsData.from_dict(_data)

        phone = d.pop("phone", UNSET)

        provider = d.pop("provider", UNSET)

        signup_params = cls(
            email=email,
            password=password,
            aud=aud,
            channel=channel,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            data=data,
            phone=phone,
            provider=provider,
        )

        signup_params.additional_properties = d
        return signup_params

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
