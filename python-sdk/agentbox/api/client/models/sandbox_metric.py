import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SandboxMetric")


@_attrs_define
class SandboxMetric:
    """Metric entry with timestamp and line

    Attributes:
        cpu_count (int): Number of CPU cores
        cpu_used_pct (float): CPU usage percentage
        mem_total_mi_b (int): Total memory in MiB
        mem_used_mi_b (int): Memory used in MiB
        timestamp (datetime.datetime): Timestamp of the metric entry
        disk_total (Union[Unset, int]): Total disk space in bytes
        disk_used (Union[Unset, int]): Disk used in bytes
        mem_total (Union[Unset, int]): Total memory in bytes
        mem_used (Union[Unset, int]): Memory used in bytes
    """

    cpu_count: int
    cpu_used_pct: float
    mem_total_mi_b: int
    mem_used_mi_b: int
    timestamp: datetime.datetime
    disk_total: Union[Unset, int] = UNSET
    disk_used: Union[Unset, int] = UNSET
    mem_total: Union[Unset, int] = UNSET
    mem_used: Union[Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cpu_count = self.cpu_count

        cpu_used_pct = self.cpu_used_pct

        mem_total_mi_b = self.mem_total_mi_b

        mem_used_mi_b = self.mem_used_mi_b

        timestamp = self.timestamp.isoformat()

        disk_total = self.disk_total

        disk_used = self.disk_used

        mem_total = self.mem_total

        mem_used = self.mem_used

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "cpuCount": cpu_count,
                "cpuUsedPct": cpu_used_pct,
                "memTotalMiB": mem_total_mi_b,
                "memUsedMiB": mem_used_mi_b,
                "timestamp": timestamp,
            }
        )
        if disk_total is not UNSET:
            field_dict["diskTotal"] = disk_total
        if disk_used is not UNSET:
            field_dict["diskUsed"] = disk_used
        if mem_total is not UNSET:
            field_dict["memTotal"] = mem_total
        if mem_used is not UNSET:
            field_dict["memUsed"] = mem_used

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cpu_count = d.pop("cpuCount")

        cpu_used_pct = d.pop("cpuUsedPct")

        mem_total_mi_b = d.pop("memTotalMiB")

        mem_used_mi_b = d.pop("memUsedMiB")

        timestamp = isoparse(d.pop("timestamp"))

        disk_total = d.pop("diskTotal", UNSET)

        disk_used = d.pop("diskUsed", UNSET)

        mem_total = d.pop("memTotal", UNSET)

        mem_used = d.pop("memUsed", UNSET)

        sandbox_metric = cls(
            cpu_count=cpu_count,
            cpu_used_pct=cpu_used_pct,
            mem_total_mi_b=mem_total_mi_b,
            mem_used_mi_b=mem_used_mi_b,
            timestamp=timestamp,
            disk_total=disk_total,
            disk_used=disk_used,
            mem_total=mem_total,
            mem_used=mem_used,
        )

        sandbox_metric.additional_properties = d
        return sandbox_metric

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
