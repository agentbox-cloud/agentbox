from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="InstanceAuthInfo")


@_attrs_define
class InstanceAuthInfo:
    """
    Attributes:
        access_key (str): tmp access key
        access_secret_key (str): tmp access secret key
        expire_time (str): expire time for ak and sk
        instance_no (str): instance number
        user_id (str): user id
    """

    access_key: str
    access_secret_key: str
    expire_time: str
    instance_no: str
    user_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_key = self.access_key

        access_secret_key = self.access_secret_key

        expire_time = self.expire_time

        instance_no = self.instance_no

        user_id = self.user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "accessKey": access_key,
                "accessSecretKey": access_secret_key,
                "expireTime": expire_time,
                "instanceNo": instance_no,
                "userId": user_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        access_key = d.pop("accessKey")

        access_secret_key = d.pop("accessSecretKey")

        expire_time = d.pop("expireTime")

        instance_no = d.pop("instanceNo")

        user_id = d.pop("userId")

        instance_auth_info = cls(
            access_key=access_key,
            access_secret_key=access_secret_key,
            expire_time=expire_time,
            instance_no=instance_no,
            user_id=user_id,
        )

        instance_auth_info.additional_properties = d
        return instance_auth_info

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
