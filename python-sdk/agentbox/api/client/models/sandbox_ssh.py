from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SandboxSSH")


@_attrs_define
class SandboxSSH:
    """
    Attributes:
        auth_password (str): Password of instance
        connect_command (str): Command of instance
        expire_time (str): Expire time of instance
        instance_no (str): ID of instance
    """

    auth_password: str
    connect_command: str
    expire_time: str
    instance_no: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auth_password = self.auth_password

        connect_command = self.connect_command

        expire_time = self.expire_time

        instance_no = self.instance_no

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "authPassword": auth_password,
                "connectCommand": connect_command,
                "expireTime": expire_time,
                "instanceNo": instance_no,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        auth_password = d.pop("authPassword")

        connect_command = d.pop("connectCommand")

        expire_time = d.pop("expireTime")

        instance_no = d.pop("instanceNo")

        sandbox_ssh = cls(
            auth_password=auth_password,
            connect_command=connect_command,
            expire_time=expire_time,
            instance_no=instance_no,
        )

        sandbox_ssh.additional_properties = d
        return sandbox_ssh

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
