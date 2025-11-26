from abc import ABC
from dataclasses import dataclass
from typing import Optional, Dict, Union
from datetime import datetime

from httpx import Limits

from agentbox.api.client.models import SandboxState, SandboxDetail, ListedSandbox
from agentbox.api.client.types import UNSET


@dataclass
class SandboxInfo:
    """Information about a sandbox."""

    sandbox_id: str
    """Sandbox ID."""
    template_id: str
    """Template ID."""
    name: Optional[str]
    """Template name."""
    metadata: Dict[str, str]
    """Saved sandbox metadata."""
    started_at: datetime
    """Sandbox start time."""
    end_at: datetime
    """Sandbox expiration date."""
    envd_version: Optional[str]
    """Envd version."""
    _envd_access_token: Optional[str]
    """Envd access token."""

    @classmethod
    def _from_sandbox_data(
        cls,
        sandbox: Union[ListedSandbox, SandboxDetail],
        envd_access_token: Optional[str] = None,
    ):
        # Combine sandbox_id with client_id if available
        sandbox_id = sandbox.sandbox_id
        if hasattr(sandbox, 'client_id'):
            sandbox_id = f"{sandbox.sandbox_id}-{sandbox.client_id}"
        
        return cls(
            sandbox_id=sandbox_id,
            template_id=sandbox.template_id,
            name=(
                sandbox.alias if sandbox.alias is not UNSET and isinstance(sandbox.alias, str) else None
            ),
            metadata=(
                sandbox.metadata if sandbox.metadata is not UNSET and isinstance(sandbox.metadata, dict) else {}
            ),
            started_at=sandbox.started_at,
            end_at=sandbox.end_at,
            envd_version=(
                sandbox.envd_version
                if isinstance(sandbox, SandboxDetail)
                and sandbox.envd_version is not UNSET
                and isinstance(sandbox.envd_version, str)
                else None
            ),
            _envd_access_token=envd_access_token,
        )

    @classmethod
    def _from_listed_sandbox(cls, listed_sandbox: ListedSandbox):
        return cls._from_sandbox_data(listed_sandbox)

    @classmethod
    def _from_sandbox_detail(cls, sandbox_detail: SandboxDetail):
        return cls._from_sandbox_data(
            sandbox_detail,
            (
                sandbox_detail.envd_access_token
                if sandbox_detail.envd_access_token is not UNSET
                and isinstance(sandbox_detail.envd_access_token, str)
                else None
            ),
        )

@dataclass
class ListedSandbox:
    """Information about a sandbox."""

    sandbox_id: str
    """Sandbox ID."""
    template_id: str
    """Template ID."""
    name: Optional[str]
    """Template Alias."""
    state: SandboxState
    """Sandbox state."""
    cpu_count: int
    """Sandbox CPU count."""
    memory_mb: int
    """Sandbox Memory size in MB."""
    metadata: Dict[str, str]
    """Saved sandbox metadata."""
    started_at: datetime
    """Sandbox start time."""
    end_at: datetime

@dataclass
class SandboxQuery:
    """Query parameters for listing sandboxes."""

    metadata: Optional[dict[str, str]] = None
    """Filter sandboxes by metadata."""


class SandboxApiBase(ABC):
    _limits = Limits(
        max_keepalive_connections=10,
        max_connections=20,
        keepalive_expiry=20,
    )

    @staticmethod
    def _get_sandbox_id(sandbox_id: str, client_id: str) -> str:
        return f"{sandbox_id}-{client_id}"
