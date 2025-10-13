import urllib.parse

from typing import Optional, Dict, List
from packaging.version import Version


from agentbox.sandbox.sandbox_api import SandboxInfo, SandboxApiBase, SandboxQuery, ListedSandbox
from agentbox.exceptions import TemplateException
from agentbox.api import AsyncApiClient, SandboxCreateResponse
from agentbox.api.client.models import NewSandbox, PostSandboxesSandboxIDTimeoutBody, SandboxADB, SandboxADBPublicInfo, SandboxSSH, InstanceAuthInfo, ResumedSandbox
from agentbox.api.client.api.sandboxes import (
    get_sandboxes_sandbox_id,
    post_sandboxes_sandbox_id_timeout,
    get_sandboxes,
    delete_sandboxes_sandbox_id,
    post_sandboxes,
    get_sandboxes_sandbox_id_adb,
    get_sandboxes_sandbox_id_ssh,
    get_sandboxes_sandbox_id_instance_no,
    get_sandboxes_sandbox_id_instance_auth_info,
    get_sandboxes_sandbox_id_adb_public_info,
    post_sandboxes_sandbox_id_pause,
    post_sandboxes_sandbox_id_resume,
)
from agentbox.connection_config import ConnectionConfig, ProxyTypes
from agentbox.api import handle_api_exception


class SandboxApi(SandboxApiBase):
    @classmethod
    async def list(
        cls,
        api_key: Optional[str] = None,
        query: Optional[SandboxQuery] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> List[ListedSandbox]:
        """
        List all running sandboxes.

        :param api_key: API key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param query: Filter the list of sandboxes, e.g. by metadata `SandboxQuery(metadata={"key": "value"})`, if there are multiple filters they are combined with AND.
        :param domain: Domain to use for the request, only relevant for self-hosted environments
        :param debug: Enable debug mode, all requested are then sent to localhost
        :param request_timeout: Timeout for the request in **seconds**
        :param headers: Additional headers to send with the request
        :param proxy: Proxy to use for the request

        :return: List of running sandboxes
        """
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=headers,
            proxy=proxy,
        )

        # Convert filters to the format expected by the API
        metadata = None
        if query:
            if query.metadata:
                quoted_metadata = {
                    urllib.parse.quote(k): urllib.parse.quote(v)
                    for k, v in query.metadata.items()
                }
                metadata = urllib.parse.urlencode(quoted_metadata)

        async with AsyncApiClient(
            config,
            limits=SandboxApiBase._limits,
        ) as api_client:
            res = await get_sandboxes.asyncio_detailed(
                client=api_client,
                metadata=metadata,
            )

        if res.status_code >= 300:
            raise handle_api_exception(res)

        if res.parsed is None:
            return []

        return [
            ListedSandbox(
                sandbox_id=SandboxApi._get_sandbox_id(
                    sandbox.sandbox_id,
                    sandbox.client_id,
                ),
                template_id=sandbox.template_id,
                name=sandbox.alias if isinstance(sandbox.alias, str) else None,
                metadata=(
                    sandbox.metadata if isinstance(sandbox.metadata, dict) else {}
                ),
                state=sandbox.state,
                cpu_count=sandbox.cpu_count,
                memory_mb=sandbox.memory_mb,
                started_at=sandbox.started_at,
                end_at=sandbox.end_at,
            )
            for sandbox in res.parsed
        ]

    @classmethod
    async def get_info(
        cls,
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> SandboxInfo:
        """
        Get the sandbox info.
        :param sandbox_id: Sandbox ID
        :param api_key: API key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param domain: Domain to use for the request, defaults to `AGENTBOX_DOMAIN` environment variable
        :param debug: Debug mode, defaults to `AGENTBOX_DEBUG` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param headers: Additional headers to send with the request
        :param proxy: Proxy to use for the request

        :return: Sandbox info
        """
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=headers,
            proxy=proxy,
        )

        async with AsyncApiClient(
            config,
            limits=SandboxApiBase._limits,
        ) as api_client:
            res = await get_sandboxes_sandbox_id.asyncio_detailed(
                sandbox_id,
                client=api_client,
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

            if res.parsed is None:
                raise Exception("Body of the request is None")

            return SandboxInfo(
                sandbox_id=SandboxApi._get_sandbox_id(
                    res.parsed.sandbox_id,
                    res.parsed.client_id,
                ),
                template_id=res.parsed.template_id,
                name=res.parsed.alias if isinstance(res.parsed.alias, str) else None,
                metadata=(
                    res.parsed.metadata if isinstance(res.parsed.metadata, dict) else {}
                ),
                started_at=res.parsed.started_at,
                end_at=res.parsed.end_at,
                envd_version=res.parsed.envd_version,
                _envd_access_token=res.parsed.envd_access_token,
            )
        
    @classmethod
    async def get_instance_no(
        cls,
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> SandboxInfo:
        """
        Get the sandbox instance number.
        :param sandbox_id: Sandbox ID
        :param api_key: API key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param domain: Domain to use for the request, defaults to `AGENTBOX_DOMAIN` environment variable
        :param debug: Debug mode, defaults to `AGENTBOX_DEBUG` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param headers: Additional headers to send with the request
        :param proxy: Proxy to use for the request

        :return: Sandbox instance number
        """
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=headers,
            proxy=proxy,
        )

        async with AsyncApiClient(
            config,
            limits=SandboxApiBase._limits,
        ) as api_client:
            res = await get_sandboxes_sandbox_id_instance_no.asyncio_detailed(
                sandbox_id,
                client=api_client,
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

            if res.parsed is None:
                raise Exception("Body of the request is None")

            return res.parsed
        
    @classmethod
    async def get_instance_auth_info(
        cls,
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[ProxyTypes] = None,
        valid_time: Optional[int] = None,
    ) -> InstanceAuthInfo:
        """
        Get the sandbox instance auth info(userId, instanceNo, accessKey, accessSecretKey, expireTime).
        :param sandbox_id: Sandbox ID
        :param api_key: API key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param domain: Domain to use for the request, defaults to `AGENTBOX_DOMAIN` environment variable
        :param debug: Debug mode, defaults to `AGENTBOX_DEBUG` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param headers: Additional headers to send with the request

        :return: Sandbox instance auth info
        """
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=headers,
            proxy=proxy,
        )

        async with AsyncApiClient(
            config,
            limits=SandboxApiBase._limits,
        ) as api_client:
            res = await get_sandboxes_sandbox_id_instance_auth_info.asyncio_detailed(
                sandbox_id,
                client=api_client,
                valid_time=valid_time,
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

            if res.parsed is None:
                raise Exception("Body of the request is None")

            return res.parsed


    @classmethod
    async def _get_adb(
        cls,
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> SandboxADB:
        """
        Get the sandbox ADB information.
        :param sandbox_id: Sandbox ID
        :param api_key: API key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param domain: Domain to use for the request, defaults to `AGENTBOX_DOMAIN` environment variable
        :param debug: Debug mode, defaults to `AGENTBOX_DEBUG` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param headers: Additional headers to send with the request
        :param proxy: Proxy to use for the request

        :return: Sandbox ADB info
        """
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=headers,
            proxy=proxy,
        )

        async with AsyncApiClient(
            config,
            limits=SandboxApiBase._limits,
        ) as api_client:
            res = await get_sandboxes_sandbox_id_adb.asyncio_detailed(
                sandbox_id,
                client=api_client,
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

            if res.parsed is None:
                raise Exception("Body of the request is None")

            return res.parsed
        
    @classmethod
    async def _get_adb_public_info(
        cls,
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> SandboxADBPublicInfo:
        """
        Get the sandbox ADB public information.
        :param sandbox_id: Sandbox ID
        :param api_key: API key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param domain: Domain to use for the request, defaults to `AGENTBOX_DOMAIN` environment variable
        :param debug: Debug mode, defaults to `AGENTBOX_DEBUG` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param headers: Additional headers to send with the request
        :param proxy: Proxy to use for the request

        :return: Sandbox ADB info
        """
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=headers,
            proxy=proxy,
        )

        async with AsyncApiClient(
            config,
            limits=cls._limits,
        ) as api_client:
            res = await get_sandboxes_sandbox_id_adb_public_info.asyncio_detailed(
                sandbox_id,
                client=api_client,
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

            if res.parsed is None:
                raise Exception("Body of the request is None")

            return res.parsed

    @classmethod
    async def _get_ssh(
        cls,
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> SandboxSSH:
        """
        Get the sandbox SSH information.
        :param sandbox_id: Sandbox ID
        :param api_key: API key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param domain: Domain to use for the request, defaults to `AGENTBOX_DOMAIN` environment variable
        :param debug: Debug mode, defaults to `AGENTBOX_DEBUG` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param headers: Additional headers to send with the request
        :param proxy: Proxy to use for the request

        :return: Sandbox SSH info
        """
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=headers,
            proxy=proxy,
        )

        async with AsyncApiClient(
            config,
            limits=SandboxApiBase._limits,
        ) as api_client:
            res = await get_sandboxes_sandbox_id_ssh.asyncio_detailed(
                sandbox_id,
                client=api_client,
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

            if res.parsed is None:
                raise Exception("Body of the request is None")

            return res.parsed

    @classmethod
    async def _cls_kill(
        cls,
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> bool:
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=headers,
            proxy=proxy,
        )

        if config.debug:
            # Skip killing the sandbox in debug mode
            return True

        async with AsyncApiClient(
            config,
            limits=SandboxApiBase._limits,
        ) as api_client:
            res = await delete_sandboxes_sandbox_id.asyncio_detailed(
                sandbox_id,
                client=api_client,
            )

            if res.status_code == 404:
                return False

            if res.status_code >= 300:
                raise handle_api_exception(res)

            return True

    @classmethod
    async def _cls_set_timeout(
        cls,
        sandbox_id: str,
        timeout: int,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> None:
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=headers,
            proxy=proxy,
        )

        if config.debug:
            # Skip setting the timeout in debug mode
            return

        async with AsyncApiClient(
            config,
            limits=SandboxApiBase._limits,
        ) as api_client:
            res = await post_sandboxes_sandbox_id_timeout.asyncio_detailed(
                sandbox_id,
                client=api_client,
                body=PostSandboxesSandboxIDTimeoutBody(timeout=timeout),
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

    @classmethod
    async def _create_sandbox(
        cls,
        template: str,
        timeout: int,
        metadata: Optional[Dict[str, str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        secure: Optional[bool] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        headers: Optional[Dict[str, str]] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> SandboxCreateResponse:
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=headers,
            proxy=proxy,
        )

        async with AsyncApiClient(
            config,
            limits=SandboxApiBase._limits,
        ) as api_client:
            res = await post_sandboxes.asyncio_detailed(
                body=NewSandbox(
                    template_id=template,
                    metadata=metadata or {},
                    timeout=timeout,
                    env_vars=env_vars or {},
                    secure=secure or False,
                ),
                client=api_client,
            )

            if res.status_code >= 300:
                raise handle_api_exception(res)

            if res.parsed is None:
                raise Exception("Body of the request is None")

            if Version(res.parsed.envd_version) < Version("0.1.0"):
                await SandboxApi._cls_kill(
                    SandboxApi._get_sandbox_id(
                        res.parsed.sandbox_id,
                        res.parsed.client_id,
                    )
                )
                raise TemplateException(
                    "You need to update the template to use the new SDK. "
                    "You can do this by running `agentbox template build` in the directory with the template."
                )

            return SandboxCreateResponse(
                sandbox_id=SandboxApi._get_sandbox_id(
                    res.parsed.sandbox_id,
                    res.parsed.client_id,
                ),
                envd_version=res.parsed.envd_version,
                envd_access_token=res.parsed.envd_access_token,
            )

    @classmethod
    async def _cls_resume(
        cls,
        sandbox_id: str,
        timeout: int,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
    ) -> bool:
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
        )

        async with AsyncApiClient(config,limits=SandboxApiBase._limits) as api_client:
            res = await post_sandboxes_sandbox_id_resume.asyncio_detailed(
                sandbox_id,
                client=api_client,
                body=ResumedSandbox(timeout=timeout),
            )

            if res.status_code == 404:
                raise Exception(f"Paused sandbox {sandbox_id} not found")

            if res.status_code == 409:
                return False

            if res.status_code >= 300:
                raise handle_api_exception(res)

            return True

    @classmethod
    async def _cls_pause(
        cls,
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
    ) -> bool:
        config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
        )

        async with AsyncApiClient(config,limits=SandboxApiBase._limits) as api_client:
            res = await post_sandboxes_sandbox_id_pause.asyncio_detailed(
                sandbox_id,
                client=api_client,
            )

            if res.status_code == 404:
                raise Exception(f"Sandbox {sandbox_id} not found")

            if res.status_code == 409:
                return False

            if res.status_code >= 300:
                raise handle_api_exception(res)

            return True