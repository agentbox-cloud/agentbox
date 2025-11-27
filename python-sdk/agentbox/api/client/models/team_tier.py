from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="TeamTier")


@_attrs_define
class TeamTier:
    """
    Attributes:
        current_instances (int): Current running instances number of team
        disk_mb (int): Max disk space of template
        id (str): Identifier of the tier
        max_hours (int): Max length hours of template
        max_instances (int): Max number of instances of team
        max_rammb (int): Max ram of template
        max_vcpu (int): Max cpu of template
        name (str): Name of the tier
        team_id (str): Identifier of the team
    """

    current_instances: int
    disk_mb: int
    id: str
    max_hours: int
    max_instances: int
    max_rammb: int
    max_vcpu: int
    name: str
    team_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        current_instances = self.current_instances

        disk_mb = self.disk_mb

        id = self.id

        max_hours = self.max_hours

        max_instances = self.max_instances

        max_rammb = self.max_rammb

        max_vcpu = self.max_vcpu

        name = self.name

        team_id = self.team_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "currentInstances": current_instances,
                "diskMB": disk_mb,
                "id": id,
                "maxHours": max_hours,
                "maxInstances": max_instances,
                "maxRAMMB": max_rammb,
                "maxVCPU": max_vcpu,
                "name": name,
                "teamID": team_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        current_instances = d.pop("currentInstances")

        disk_mb = d.pop("diskMB")

        id = d.pop("id")

        max_hours = d.pop("maxHours")

        max_instances = d.pop("maxInstances")

        max_rammb = d.pop("maxRAMMB")

        max_vcpu = d.pop("maxVCPU")

        name = d.pop("name")

        team_id = d.pop("teamID")

        team_tier = cls(
            current_instances=current_instances,
            disk_mb=disk_mb,
            id=id,
            max_hours=max_hours,
            max_instances=max_instances,
            max_rammb=max_rammb,
            max_vcpu=max_vcpu,
            name=name,
            team_id=team_id,
        )

        team_tier.additional_properties = d
        return team_tier

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
