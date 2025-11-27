from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.alert_context_common_annotations import AlertContextCommonAnnotations
    from ..models.alert_context_common_labels import AlertContextCommonLabels


T = TypeVar("T", bound="AlertContext")


@_attrs_define
class AlertContext:
    r"""
    Example:
        {'commonAnnotations': {'cpu_used': '>50%', 'description': 'sum(nomad_client_host_cpu_total) /
            (sum(nomad_client_host_cpu_total) + sum(nomad_client_host_cpu_idle))', 'summary': '集群CPU使用率大于50%'}, 'message':
            '**Firing**\nValue: A=0.04', 'state': 'alerting', 'title': '[FIRING:1] DatasourceNoData api-alter-rule
            (bey8l1jmgkbnkb A 集群CUP监控)'}

    Attributes:
        message (str): Alert message (may contain markdown)
        state (str): Alert state (e.g., alerting, ok)
        title (str): Alert title
        common_annotations (Union[Unset, AlertContextCommonAnnotations]): Common annotations for the alert (key/value
            string map)
        common_labels (Union[Unset, AlertContextCommonLabels]): Common labels for the alert (key/value string map)
    """

    message: str
    state: str
    title: str
    common_annotations: Union[Unset, "AlertContextCommonAnnotations"] = UNSET
    common_labels: Union[Unset, "AlertContextCommonLabels"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        state = self.state

        title = self.title

        common_annotations: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.common_annotations, Unset):
            common_annotations = self.common_annotations.to_dict()

        common_labels: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.common_labels, Unset):
            common_labels = self.common_labels.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "message": message,
                "state": state,
                "title": title,
            }
        )
        if common_annotations is not UNSET:
            field_dict["commonAnnotations"] = common_annotations
        if common_labels is not UNSET:
            field_dict["commonLabels"] = common_labels

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.alert_context_common_annotations import AlertContextCommonAnnotations
        from ..models.alert_context_common_labels import AlertContextCommonLabels

        d = dict(src_dict)
        message = d.pop("message")

        state = d.pop("state")

        title = d.pop("title")

        _common_annotations = d.pop("commonAnnotations", UNSET)
        common_annotations: Union[Unset, AlertContextCommonAnnotations]
        if isinstance(_common_annotations, Unset):
            common_annotations = UNSET
        else:
            common_annotations = AlertContextCommonAnnotations.from_dict(_common_annotations)

        _common_labels = d.pop("commonLabels", UNSET)
        common_labels: Union[Unset, AlertContextCommonLabels]
        if isinstance(_common_labels, Unset):
            common_labels = UNSET
        else:
            common_labels = AlertContextCommonLabels.from_dict(_common_labels)

        alert_context = cls(
            message=message,
            state=state,
            title=title,
            common_annotations=common_annotations,
            common_labels=common_labels,
        )

        alert_context.additional_properties = d
        return alert_context

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
