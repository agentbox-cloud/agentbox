from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SandboxADBPublicInfo")


@_attrs_define
class SandboxADBPublicInfo:
    """
    Attributes:
        adb_ip (str): IP or HOST of instance adb connection
        adb_port (int): Port of instance adb connection
        expire_time (str): Expire time of instance
        instance_no (str): ID of instance
        private_key (str): PrivateKey to connect instance
        public_key (str): PublicKey to connect instance
    """

    adb_ip: str
    adb_port: int
    expire_time: str
    instance_no: str
    private_key: str
    public_key: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        adb_ip = self.adb_ip

        adb_port = self.adb_port

        expire_time = self.expire_time

        instance_no = self.instance_no

        private_key = self.private_key

        public_key = self.public_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "adbIp": adb_ip,
                "adbPort": adb_port,
                "expireTime": expire_time,
                "instanceNo": instance_no,
                "privateKey": private_key,
                "publicKey": public_key,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        adb_ip = d.pop("adbIp")

        adb_port = d.pop("adbPort")

        expire_time = d.pop("expireTime")

        instance_no = d.pop("instanceNo")

        private_key = d.pop("privateKey")

        public_key = d.pop("publicKey")

        sandbox_adb_public_info = cls(
            adb_ip=adb_ip,
            adb_port=adb_port,
            expire_time=expire_time,
            instance_no=instance_no,
            private_key=private_key,
            public_key=public_key,
        )

        sandbox_adb_public_info.additional_properties = d
        return sandbox_adb_public_info

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
