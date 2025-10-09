from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SandboxADB")


@_attrs_define
class SandboxADB:
    """
    Attributes:
        adb_auth_command (str): Command of adb auth
        auth_password (str): Password of instance
        connect_command (str): Command of instance
        expire_time (str): Expire time of instance
        forwarder_command (str): Command of forwarder
        instance_no (str): ID of instance
    """

    adb_auth_command: str
    auth_password: str
    connect_command: str
    expire_time: str
    forwarder_command: str
    instance_no: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        adb_auth_command = self.adb_auth_command

        auth_password = self.auth_password

        connect_command = self.connect_command

        expire_time = self.expire_time

        forwarder_command = self.forwarder_command

        instance_no = self.instance_no

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "adbAuthCommand": adb_auth_command,
                "authPassword": auth_password,
                "connectCommand": connect_command,
                "expireTime": expire_time,
                "forwarderCommand": forwarder_command,
                "instanceNo": instance_no,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        adb_auth_command = d.pop("adbAuthCommand")

        auth_password = d.pop("authPassword")

        connect_command = d.pop("connectCommand")

        expire_time = d.pop("expireTime")

        forwarder_command = d.pop("forwarderCommand")

        instance_no = d.pop("instanceNo")

        sandbox_adb = cls(
            adb_auth_command=adb_auth_command,
            auth_password=auth_password,
            connect_command=connect_command,
            expire_time=expire_time,
            forwarder_command=forwarder_command,
            instance_no=instance_no,
        )

        sandbox_adb.additional_properties = d
        return sandbox_adb

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
