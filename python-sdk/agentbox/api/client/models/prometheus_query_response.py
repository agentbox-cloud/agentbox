from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.prometheus_query_response_data import PrometheusQueryResponseData


T = TypeVar("T", bound="PrometheusQueryResponse")


@_attrs_define
class PrometheusQueryResponse:
    """
    Attributes:
        data (PrometheusQueryResponseData): Prometheus response data (varies by query)
        status (str): Response status (e.g., "success")
    """

    data: "PrometheusQueryResponseData"
    status: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = self.data.to_dict()

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "status": status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.prometheus_query_response_data import PrometheusQueryResponseData

        d = dict(src_dict)
        data = PrometheusQueryResponseData.from_dict(d.pop("data"))

        status = d.pop("status")

        prometheus_query_response = cls(
            data=data,
            status=status,
        )

        prometheus_query_response.additional_properties = d
        return prometheus_query_response

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
