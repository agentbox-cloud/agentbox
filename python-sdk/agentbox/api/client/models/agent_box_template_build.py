from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.agent_box_template_build_status import AgentBoxTemplateBuildStatus

T = TypeVar("T", bound="AgentBoxTemplateBuild")


@_attrs_define
class AgentBoxTemplateBuild:
    """
    Attributes:
        build_id (str): Identifier of the build
        logs (str): Build logs Default: 'string'.
        status (AgentBoxTemplateBuildStatus): Status of the template
        template_id (str): Identifier of the template
    """

    build_id: str
    status: AgentBoxTemplateBuildStatus
    template_id: str
    logs: str = "string"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        build_id = self.build_id

        logs = self.logs

        status = self.status.value

        template_id = self.template_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "buildID": build_id,
                "logs": logs,
                "status": status,
                "templateID": template_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        build_id = d.pop("buildID")

        logs = d.pop("logs")

        status = AgentBoxTemplateBuildStatus(d.pop("status"))

        template_id = d.pop("templateID")

        agent_box_template_build = cls(
            build_id=build_id,
            logs=logs,
            status=status,
            template_id=template_id,
        )

        agent_box_template_build.additional_properties = d
        return agent_box_template_build

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
