import logging
import httpx
import re
import uuid
import json
from datetime import datetime

from typing import Dict, Optional, TypedDict, overload, List, Union
from typing_extensions import Unpack, Self
from packaging.version import Version

from agentbox.api.client.types import Unset
from agentbox.connection_config import ConnectionConfig, ProxyTypes, ApiParams
from agentbox.envd.api import ENVD_API_HEALTH_ROUTE, ahandle_envd_api_exception
from agentbox.exceptions import format_request_timeout_error, SandboxException
from agentbox.sandbox.main import SandboxSetup
from agentbox.sandbox.utils import class_method_variant
from agentbox.sandbox.sandbox_api import SandboxMetrics
from agentbox.sandbox_async.adb_shell.adb_shell import ADBShell
from agentbox.sandbox_async.filesystem.filesystem import Filesystem
from agentbox.sandbox_async.commands.command import Commands
from agentbox.sandbox_async.commands.pty import Pty
from agentbox.sandbox_async.sandbox_api import SandboxApi, SandboxInfo
from agentbox.api.client.models import InstanceAuthInfo
from agentbox.sandbox_async.filesystem_ssh.filesystem_ssh import SSHFilesystem
from agentbox.sandbox_async.commands_ssh.command_ssh import SSHCommands
from agentbox.sandbox_async.commands_ssh2.command_ssh2 import SSHCommands2

logger = logging.getLogger(__name__)


class AsyncTransportWithLogger(httpx.AsyncHTTPTransport):
    async def handle_async_request(self, request):
        url = f"{request.url.scheme}://{request.url.host}{request.url.path}"
        logger.info(f"Request: {request.method} {url}")
        response = await super().handle_async_request(request)

        # data = connect.GzipCompressor.decompress(response.read()).decode()
        logger.info(f"Response: {response.status_code} {url}")

        return response


class AsyncSandboxOpts(TypedDict):
    sandbox_id: str
    envd_version: Optional[str]
    envd_access_token: Optional[str]
    connection_config: ConnectionConfig
    # optional field
    ssh_host: Optional[str]
    ssh_port: Optional[int]
    ssh_username: Optional[str]
    ssh_password: Optional[str]
    adb_auth_command: Optional[str]
    adb_auth_password: Optional[str]
    adb_connect_command: Optional[str]
    adb_forwarder_command: Optional[str]


class AsyncSandbox(SandboxSetup, SandboxApi):
    """
    E2B cloud sandbox is a secure and isolated cloud environment.

    The sandbox allows you to:
    - Access Linux OS
    - Create, list, and delete files and directories
    - Run commands
    - Run isolated code
    - Access the internet

    Check docs [here](https://agentbox.cloud/docs).

    Use the `AsyncSandbox.create()` to create a new sandbox.

    Example:
    ```python
    from agentbox import AsyncSandbox

    sandbox = await AsyncSandbox.create()
    ```
    """

    @property
    def files(self) -> Filesystem:
        """
        Module for interacting with the sandbox filesystem.
        """
        return self._filesystem

    @property
    def commands(self) -> Commands:
        """
        Module for running commands in the sandbox.
        """
        return self._commands

    @property
    def pty(self) -> Pty:
        """
        Module for interacting with the sandbox pseudo-terminal.
        """
        if not hasattr(self, '_pty') or self._pty is None:
            raise AttributeError(
                "PTY is not available for this sandbox type. "
                "PTY is only available for standard sandboxes, not SSH-based sandboxes."
            )
        return self._pty

    @property
    def sandbox_id(self) -> str:
        """
        Unique identifier of the sandbox.
        """
        return self._sandbox_id

    @property
    def envd_api_url(self) -> str:
        return self._envd_api_url

    @property
    def adb_shell(self) -> ADBShell:
        """
        Module for adb shell in the sandbox.
        """
        return self._adb_shell

    @property
    def _envd_access_token(self) -> str:
        """Private property to access the envd token"""
        return self.__envd_access_token

    @_envd_access_token.setter
    def _envd_access_token(self, value: str):
        """Private setter for envd token"""
        self.__envd_access_token = value

    # @property
    # def envd_version(self) -> str:
    #     return self._envd_version
    # @envd_version.setter
    # def envd_version(self, value: str):
    #     self._envd_version = value

    @property
    def connection_config(self) -> ConnectionConfig:
        return self._connection_config

    def __init__(self, **opts: Unpack[AsyncSandboxOpts]):
        """
        Use `AsyncSandbox.create()` to create a new sandbox instead.
        """
        super().__init__()

        self._sandbox_id = opts["sandbox_id"]
        self._connection_config = opts["connection_config"]
        # Optional fields
        self._ssh_host = opts.get("ssh_host")
        self._ssh_port = opts.get("ssh_port")
        self._ssh_username = opts.get("ssh_username")
        self._ssh_password = opts.get("ssh_password")
        self._adb_auth_command = opts.get("adb_auth_command")
        self._adb_auth_password = opts.get("adb_auth_password")
        self._adb_connect_command = opts.get("adb_connect_command")
        self._adb_forwarder_command = opts.get("adb_forwarder_command")

        self._envd_api_url = f"{'http' if self.connection_config.debug else 'https'}://{self.get_host(self.envd_port)}"
        envd_version = opts.get("envd_version")
        if envd_version is not None:
            self._envd_version = Version(envd_version) if isinstance(envd_version, str) else envd_version
        
        self._envd_access_token = opts.get("envd_access_token")

        # 根据 sandbox id 进行区分 commands 类型
        if "brd" in self._sandbox_id.lower():
            # self._commands = SSHCommands(
            #     self._ssh_host,
            #     self._ssh_port,
            #     self._ssh_username,
            #     self._ssh_password,
            #     self.connection_config,
            # )
            self._commands = SSHCommands2(
                self._ssh_host,
                self._ssh_port,
                self._ssh_username,
                self._ssh_password,
                self.connection_config,
            )
            # self._watch_commands = SSHCommands(
            #     self._ssh_host,
            #     self._ssh_port,
            #     self._ssh_username,
            #     self._ssh_password,
            #     self.connection_config,
            # )
            self._watch_commands = SSHCommands2(
                self._ssh_host,
                self._ssh_port,
                self._ssh_username,
                self._ssh_password,
                self.connection_config,
            )
            self._filesystem = SSHFilesystem(
                self._ssh_host,
                self._ssh_port,
                self._ssh_username,
                self._ssh_password,
                self.connection_config,
                self._commands,
                self._watch_commands,
            )
            self._adb_shell = ADBShell(
                connection_config=self.connection_config,
                sandbox_id=self._sandbox_id
            )
        else:
            self._transport = AsyncTransportWithLogger(
                limits=self._limits, proxy=self._connection_config.proxy
            )
            self._envd_api = httpx.AsyncClient(
                base_url=self.envd_api_url,
                transport=self._transport,
                headers=self._connection_config.headers,
            )

            self._filesystem = Filesystem(
                self.envd_api_url,
                str(self._envd_version) if self._envd_version is not None else None,
                self.connection_config,
                self._transport._pool,
                self._envd_api,
            )
            self._commands = Commands(
                self.envd_api_url,
                self.connection_config,
                self._transport._pool,
            )
            self._pty = Pty(
                self.envd_api_url,
                self.connection_config,
                self._transport._pool,
            )

    async def is_running(self, request_timeout: Optional[float] = None) -> bool:
        """
        Check if the sandbox is running.

        :param request_timeout: Timeout for the request in **seconds**

        :return: `True` if the sandbox is running, `False` otherwise

        Example
        ```python
        sandbox = await AsyncSandbox.create()
        await sandbox.is_running() # Returns True

        await sandbox.kill()
        await sandbox.is_running() # Returns False
        ```
        """
        # For brd type sandboxes, _envd_api is not initialized
        if not hasattr(self, '_envd_api') or self._envd_api is None:
            # For SSH-based sandboxes, we assume they are running if we can connect
            # This is a simplified check - in practice you might want to verify SSH connection
            return True
        
        try:
            r = await self._envd_api.get(
                ENVD_API_HEALTH_ROUTE,
                timeout=self.connection_config.get_request_timeout(request_timeout),
            )

            if r.status_code == 502:
                return False

            err = await ahandle_envd_api_exception(r)

            if err:
                raise err

        except httpx.TimeoutException:
            raise format_request_timeout_error()

        return True

    @classmethod
    async def create(
        cls,
        template: Optional[str] = None,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None,
        envs: Optional[Dict[str, str]] = None,
        secure: Optional[bool] = None,
        **opts: Unpack[ApiParams],
    ) -> Self:
        """
        Create a new sandbox.

        By default, the sandbox is created from the default `base` sandbox template.

        :param template: Sandbox template name or ID
        :param timeout: Timeout for the sandbox in **seconds**, default to 300 seconds. Maximum time a sandbox can be kept alive is 24 hours (86_400 seconds) for Pro users and 1 hour (3_600 seconds) for Hobby users.
        :param metadata: Custom metadata for the sandbox
        :param envs: Custom environment variables for the sandbox
        :param api_key: E2B API Key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request and for the **requests made to the returned sandbox**
        :param secure: Envd is secured with access token and cannot be used without it

        :return: sandbox instance for the new sandbox

        Use this method instead of using the constructor to create a new sandbox.
        """
        return await cls._create(
            template=template,
            timeout=timeout,
            auto_pause=False,
            metadata=metadata,
            envs=envs,
            secure=secure or False,
            **opts,
        )

    @overload
    async def connect(
        self,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ) -> Self:
        """
        Connect to a sandbox. If the sandbox is paused, it will be automatically resumed.
        Sandbox must be either running or be paused.

        With sandbox ID you can connect to the same sandbox from different places or environments (serverless functions, etc).

        :param timeout: Timeout for the sandbox in **seconds**.
            For running sandboxes, the timeout will update only if the new timeout is longer than the existing one.
        :param request_timeout: Timeout for the request in **seconds**
        :return: A running sandbox instance

        @example
        ```python
        sandbox = await AsyncSandbox.create()
        await sandbox.pause()

        # Another code block
        same_sandbox = await sandbox.connect()
        ```
        """
        ...

    @overload
    @classmethod
    async def connect(
        cls,
        sandbox_id: str,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ) -> Self:
        """
        Connect to a sandbox. If the sandbox is paused, it will be automatically resumed.
        Sandbox must be either running or be paused.

        With sandbox ID you can connect to the same sandbox from different places or environments (serverless functions, etc).

        :param sandbox_id: Sandbox ID
        :param timeout: Timeout for the sandbox in **seconds**.
            For running sandboxes, the timeout will update only if the new timeout is longer than the existing one.
        :param api_key: E2B API Key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param domain: Domain of the sandbox server
        :param debug: Enable debug mode
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request and for the **requests made to the returned sandbox**
        :return: A running sandbox instance

        @example
        ```python
        sandbox = await AsyncSandbox.create()
        await AsyncSandbox.pause(sandbox.sandbox_id)

        # Another code block
        same_sandbox = await AsyncSandbox.connect(sandbox.sandbox_id)
        ```
        """
        ...

    @class_method_variant("_cls_connect")
    async def connect(
        self,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ) -> Self:
        """
        Connect to a sandbox. If the sandbox is paused, it will be automatically resumed.
        Sandbox must be either running or be paused.

        With sandbox ID you can connect to the same sandbox from different places or environments (serverless functions, etc).

        :param timeout: Timeout for the sandbox in **seconds**.
            For running sandboxes, the timeout will update only if the new timeout is longer than the existing one.
        :param request_timeout: Timeout for the request in **seconds**
        :return: A running sandbox instance

        @example
        ```python
        sandbox = await AsyncSandbox.create()
        await sandbox.pause()

        # Another code block
        same_sandbox = await sandbox.connect()
        ```
        """
        return await self.__class__._cls_connect(
            sandbox_id=self.sandbox_id,
            timeout=timeout,
            **self.connection_config.get_api_params(**opts),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.kill()

    @overload
    async def kill(self, **opts: Unpack[ApiParams]) -> bool:
        """
        Kill the sandbox.

        :param request_timeout: Timeout for the request in **seconds**

        :return: `True` if the sandbox was killed, `False` if the sandbox was not found
        """
        ...

    @overload
    @staticmethod
    async def kill(
        sandbox_id: str,
        **opts: Unpack[ApiParams],
    ) -> bool:
        """
        Kill the sandbox specified by sandbox ID.

        :param sandbox_id: Sandbox ID
        :param api_key: E2B API Key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request

        :return: `True` if the sandbox was killed, `False` if the sandbox was not found
        """
        ...

    @class_method_variant("_cls_kill")
    async def kill(
        self,
        **opts: Unpack[ApiParams],
    ) -> bool:  
        """
        Kill the sandbox.

        :param request_timeout: Timeout for the request
        :return: `True` if the sandbox was killed, `False` if the sandbox was not found
        """
        return await SandboxApi._cls_kill(
            sandbox_id=self.sandbox_id,
            **self.connection_config.get_api_params(**opts),
        )

    @overload
    async def set_timeout(
        self,
        timeout: int,
        **opts: Unpack[ApiParams],
    ) -> None:
        """
        Set the timeout of the sandbox.
        After the timeout expires the sandbox will be automatically killed.
        This method can extend or reduce the sandbox timeout set when creating the sandbox or from the last call to `.set_timeout`.

        Maximum time a sandbox can be kept alive is 24 hours (86_400 seconds) for Pro users and 1 hour (3_600 seconds) for Hobby users.

        :param timeout: Timeout for the sandbox in **seconds**
        :param request_timeout: Timeout for the request in **seconds**
        """
        ...

    @overload
    @staticmethod
    async def set_timeout(
        sandbox_id: str,
        timeout: int,
        **opts: Unpack[ApiParams],
    ) -> None:
        """
        Set the timeout of the specified sandbox.
        After the timeout expires the sandbox will be automatically killed.
        This method can extend or reduce the sandbox timeout set when creating the sandbox or from the last call to `.set_timeout`.

        Maximum time a sandbox can be kept alive is 24 hours (86_400 seconds) for Pro users and 1 hour (3_600 seconds) for Hobby users.

        :param sandbox_id: Sandbox ID
        :param timeout: Timeout for the sandbox in **seconds**
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request
        """
        ...

    @class_method_variant("_cls_set_timeout")
    async def set_timeout(
        self,
        timeout: int,
        **opts: Unpack[ApiParams],
    ) -> None:
        """
        Set the timeout of the sandbox.
        After the timeout expires, the sandbox will be automatically killed.
        This method can extend or reduce the sandbox timeout set when creating the sandbox or from the last call to `.set_timeout`.

        Maximum time a sandbox can be kept alive is 24 hours (86_400 seconds) for Pro users and 1 hour (3_600 seconds) for Hobby users.

        :param timeout: Timeout for the sandbox in **seconds**

        """
        await SandboxApi._cls_set_timeout(
            sandbox_id=self.sandbox_id,
            timeout=timeout,
            **self.connection_config.get_api_params(**opts),
        )

    @classmethod
    async def _cls_connect(
        cls,
        sandbox_id: str,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ) -> Self:
        # Skip resume operation for "brd" sandboxes
        if "brd" in sandbox_id.lower():
            sandbox_info = await SandboxApi._cls_get_info(
                sandbox_id=sandbox_id,
                **opts,
            )
            
            connection_config = ConnectionConfig(**opts)
            
            # Get SSH connection details
            ssh_info = await SandboxApi._get_ssh(
                sandbox_id=sandbox_id,
                **opts,
            )

            # Parse SSH connection details from the connect command
            pattern = r'ssh\s+-p\s+(\d+).*?\s+([^@\s]+)@([\w\.-]+)'
            ssh_match = re.search(pattern, ssh_info.connect_command)
            if ssh_match:
                ssh_port = int(ssh_match.group(1))
                ssh_username = ssh_match.group(2)
                ssh_host = ssh_match.group(3)
                ssh_password = ssh_info.auth_password
            else:
                raise Exception("Could not parse SSH connection details")
            
            return cls(
                sandbox_id=sandbox_id,
                envd_version=sandbox_info.envd_version,
                envd_access_token=sandbox_info._envd_access_token,
                connection_config=connection_config,
                ssh_host=ssh_host,
                ssh_port=ssh_port,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
            )
        else:
            timeout = timeout or cls.default_sandbox_timeout
            sandbox = await SandboxApi._cls_connect(
                sandbox_id=sandbox_id,
                timeout=timeout,
                **opts,
            )

            connection_headers = {}
            envd_access_token = sandbox.envd_access_token
            if envd_access_token is not None and not isinstance(envd_access_token, Unset):
                connection_headers["X-Access-Token"] = envd_access_token

            connection_config = ConnectionConfig(
                extra_sandbox_headers=connection_headers,
                **opts,
            )

            return cls(
                sandbox_id=sandbox_id,
                connection_config=connection_config,
                envd_version=sandbox.envd_version,
                envd_access_token=envd_access_token,
            )

    @overload
    async def resume(
        self,
        auto_pause: bool = False,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ) -> Self:
        ...

    @overload
    @classmethod
    async def resume(
        cls,
        sandbox_id: str,
        auto_pause: bool = False,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ) -> Self:
        """
        Resume the sandbox.

        The **default sandbox timeout of 300 seconds** will be used for the resumed sandbox.
        If you pass a custom timeout via the `timeout` parameter, it will be used instead.

        :param sandbox_id: sandbox ID
        :param auto_pause: Automatically pause the sandbox after the timeout expires. Defaults to `False`.
        :param timeout: Timeout for the sandbox in **seconds**
        :param api_key: E2B API Key to use for authentication
        :param domain: Domain of the sandbox server
        :param debug: Enable debug mode
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request

        :return: A running sandbox instance
        """
        ...

    @class_method_variant("_cls_resume")
    async def resume(
        self,
        auto_pause: bool = False,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ) -> Self:
        """
        Resume the sandbox.

        The **default sandbox timeout of 300 seconds** will be used for the resumed sandbox.
        If you pass a custom timeout via the `timeout` parameter, it will be used instead.

        :param auto_pause: Automatically pause the sandbox after the timeout expires. Defaults to `False`.
        :param timeout: Timeout for the sandbox in **seconds**
        :param request_timeout: Timeout for the request in **seconds**

        :return: A running sandbox instance
        """
        return await self.__class__._cls_resume(
            sandbox_id=self.sandbox_id,
            auto_pause=auto_pause,
            timeout=timeout,
            **self.connection_config.get_api_params(**opts),
        )

    @classmethod
    async def _cls_resume(
        cls,
        sandbox_id: str,
        auto_pause: bool = False,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ) -> Self:
        # Skip resume operation for "brd" sandboxes
        if "brd" in sandbox_id.lower():
            sandbox_info = await SandboxApi._cls_get_info(
                sandbox_id=sandbox_id,
                **opts,
            )
            
            connection_config = ConnectionConfig(**opts)
            
            # Get SSH connection details
            ssh_info = await SandboxApi._get_ssh(
                sandbox_id=sandbox_id,
                **opts,
            )

            # Parse SSH connection details from the connect command
            pattern = r'ssh\s+-p\s+(\d+).*?\s+([^@\s]+)@([\w\.-]+)'
            ssh_match = re.search(pattern, ssh_info.connect_command)
            if ssh_match:
                ssh_port = int(ssh_match.group(1))
                ssh_username = ssh_match.group(2)
                ssh_host = ssh_match.group(3)
                ssh_password = ssh_info.auth_password
            else:
                raise Exception("Could not parse SSH connection details")
            
            return cls(
                sandbox_id=sandbox_id,
                envd_version=sandbox_info.envd_version,
                envd_access_token=sandbox_info._envd_access_token,
                connection_config=connection_config,
                ssh_host=ssh_host,
                ssh_port=ssh_port,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
            )
        else:
            timeout = timeout or cls.default_sandbox_timeout
            sandbox = await SandboxApi._cls_resume(
                sandbox_id=sandbox_id,
                auto_pause=auto_pause,
                timeout=timeout,
                **opts,
            )

            connection_headers = {}
            envd_access_token = sandbox.envd_access_token
            if envd_access_token is not None and not isinstance(envd_access_token, Unset):
                connection_headers["X-Access-Token"] = envd_access_token

            connection_config = ConnectionConfig(
                extra_sandbox_headers=connection_headers,
                **opts,
            )

            return cls(
                sandbox_id=sandbox_id,
                connection_config=connection_config,
                envd_version=sandbox.envd_version,
                envd_access_token=envd_access_token,
            )

    @overload
    async def pause(
        self,
        **opts: Unpack[ApiParams],
    ) -> None:
        """
        Pause the sandbox.

        :param request_timeout: Timeout for the request in **seconds**

        :return: sandbox ID that can be used to resume the sandbox
        """
        ...

    @overload
    @staticmethod
    async def pause(
        sandbox_id: str,
        **opts: Unpack[ApiParams],
    ) -> None:
        """
        Pause the sandbox specified by sandbox ID.

        :param sandbox_id: Sandbox ID
        :param api_key: E2B API Key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param request_timeout: Timeout for the request in **seconds**

        :return: sandbox ID that can be used to resume the sandbox
        """
        ...

    @class_method_variant("_cls_pause")
    async def pause(  
        self,
        **opts: Unpack[ApiParams],
    ) -> None:
        """
        Pause the sandbox.

        :param request_timeout: Timeout for the request in **seconds**

        :return: sandbox ID that can be used to resume the sandbox
        """

        await SandboxApi._cls_pause(
            sandbox_id=self.sandbox_id,
            **self.connection_config.get_api_params(**opts),
        )

    @overload
    async def get_info(
        self,
        **opts: Unpack[ApiParams],
    ) -> SandboxInfo:
        """
        Get sandbox information like sandbox ID, template, metadata, started at/end at date.

        :return: Sandbox info
        """
        ...

    @overload
    @staticmethod
    async def get_info(
        sandbox_id: str,
        **opts: Unpack[ApiParams],
    ) -> SandboxInfo:
        """
        Get sandbox information like sandbox ID, template, metadata, started at/end at date.
        :param sandbox_id: Sandbox ID

        :return: Sandbox info
        """
        ...

    @class_method_variant("_cls_get_info")
    async def get_info(
        self,
        **opts: Unpack[ApiParams],
    ) -> SandboxInfo:
        """
        Get sandbox information like sandbox ID, template, metadata, started at/end at date.

        :return: Sandbox info
        """

        return await SandboxApi._cls_get_info(
            sandbox_id=self.sandbox_id,
            **self.connection_config.get_api_params(**opts),
        )


    @overload
    async def get_metrics(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        **opts: Unpack[ApiParams],
    ) -> List[SandboxMetrics]:
        """
        Get the metrics of the current sandbox.

        :param start: Start time for the metrics in **seconds** (Unix timestamp), defaults to the start of the sandbox
        :param end: End time for the metrics in **seconds** (Unix timestamp), defaults to the current time

        :return: List of sandbox metrics containing CPU, memory and disk usage information
        """
        ...

    @overload
    @staticmethod
    async def get_metrics(
        sandbox_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        **opts: Unpack[ApiParams],
    ) -> List[SandboxMetrics]:
        """
        Get the metrics of the sandbox specified by sandbox ID.

        :param sandbox_id: Sandbox ID
        :param start: Start time for the metrics in **seconds** (Unix timestamp), defaults to the start of the sandbox
        :param end: End time for the metrics in **seconds** (Unix timestamp), defaults to the current time

        :return: List of sandbox metrics containing CPU, memory and disk usage information
        """
        ...

    @class_method_variant("_cls_get_metrics")
    async def get_metrics(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        **opts: Unpack[ApiParams],
    ) -> List[SandboxMetrics]:
        """
        Get the metrics of the current sandbox.

        :param start: Start time for the metrics in **seconds** (Unix timestamp), defaults to the start of the sandbox
        :param end: End time for the metrics in **seconds** (Unix timestamp), defaults to the current time

        :return: List of sandbox metrics containing CPU, memory and disk usage information
        """
        if self._envd_version and self._envd_version < Version("0.1.5"):
            raise SandboxException(
                "Metrics are not supported in this version of the sandbox, please rebuild your template."
            )

        if self._envd_version and self._envd_version < Version("0.2.4"):
            logger.warning(
                "Disk metrics are not supported in this version of the sandbox, please rebuild the template to get disk metrics."
            )

        return await SandboxApi._cls_get_metrics(
            sandbox_id=self.sandbox_id,
            start=start,
            end=end,
            **self.connection_config.get_api_params(**opts),
        )

    async def get_instance_no(  
        self,
        **opts: Unpack[ApiParams],
    ) -> str:
        """
        Get sandbox instance number.
        :param request_timeout: Timeout for the request in **seconds**
        :return: Sandbox instance number
        """
        return await SandboxApi.get_instance_no(
            sandbox_id=self.sandbox_id,
            **self.connection_config.get_api_params(**opts),
        )
    
    async def get_instance_auth_info(  
        self,
        valid_time: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ) -> InstanceAuthInfo:
        """
        Get sandbox instance auth info.
        :param request_timeout: Timeout for the request in **seconds**
        :return: Sandbox instance auth info
        """
        return await SandboxApi.get_instance_auth_info(
            sandbox_id=self.sandbox_id,
            valid_time=valid_time,
            **self.connection_config.get_api_params(**opts),
        )

    @classmethod
    async def beta_create(
        cls,
        template: Optional[str] = None,
        timeout: Optional[int] = None,
        auto_pause: bool = False,
        metadata: Optional[Dict[str, str]] = None,
        envs: Optional[Dict[str, str]] = None,
        secure: Optional[bool] = None,
        **opts: Unpack[ApiParams],
    ) -> Self:
        """
        [BETA] This feature is in beta and may change in the future.

        Create a new sandbox.

        By default, the sandbox is created from the default `base` sandbox template.

        :param template: Sandbox template name or ID
        :param timeout: Timeout for the sandbox in **seconds**, default to 300 seconds. The maximum time a sandbox can be kept alive is 24 hours (86_400 seconds) for Pro users and 1 hour (3_600 seconds) for Hobby users.
        :param auto_pause: Automatically pause the sandbox after the timeout expires. Defaults to `False`.
        :param metadata: Custom metadata for the sandbox
        :param envs: Custom environment variables for the sandbox
        :param secure: Envd is secured with access token and cannot be used without it, defaults to `True`.
        :param api_key: E2B API Key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param domain: Domain of the sandbox server
        :param debug: Enable debug mode
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request and for the **requests made to the returned sandbox**

        :return: A Sandbox instance for the new sandbox

        Use this method instead of using the constructor to create a new sandbox.
        """

        if not template:
            template = cls.default_template

        sandbox = await cls._create(
            template=template,
            auto_pause=auto_pause,
            timeout=timeout,
            metadata=metadata,
            envs=envs,
            secure=secure or False,
            **opts,
        )
        
        return sandbox

    @classmethod
    async def _create(
        cls,
        template: Optional[str],
        timeout: Optional[int],
        auto_pause: bool,
        metadata: Optional[Dict[str, str]],
        envs: Optional[Dict[str, str]],
        secure: bool,
        **opts: Unpack[ApiParams],
    ) -> Self:
        extra_sandbox_headers = {}

        if opts.get("debug"):
            sandbox_id = "debug_sandbox_id"
            envd_version = None
            envd_access_token = None
        else:
            response = await SandboxApi._create_sandbox(
                template=template or cls.default_template,
                timeout=timeout or cls.default_sandbox_timeout,
                auto_pause=auto_pause,
                metadata=metadata,
                env_vars=envs,
                secure=secure,
                **opts,
            )

            sandbox_id = response.sandbox_id
            envd_version = response.envd_version
            envd_access_token = response.envd_access_token

            if envd_access_token is not None and not isinstance(
                envd_access_token, Unset
            ):
                extra_sandbox_headers["X-Access-Token"] = envd_access_token

        connection_config = ConnectionConfig(
            extra_sandbox_headers=extra_sandbox_headers,
            **opts,
        )

        if "brd" in sandbox_id.lower():
            # Get SSH connection details
            ssh_info = await SandboxApi._get_ssh(
                sandbox_id=sandbox_id,
                **connection_config.get_api_params(),
            )

            # Parse SSH connection details from the connect command
            pattern = r'ssh\s+-p\s+(\d+).*?\s+([^@\s]+)@([\w\.-]+)'
            ssh_match = re.search(pattern, ssh_info.connect_command)
            if ssh_match:
                ssh_port = int(ssh_match.group(1))
                ssh_username = ssh_match.group(2)
                ssh_host = ssh_match.group(3)
                ssh_password = ssh_info.auth_password
            else:
                raise Exception("Could not parse SSH connection details")
           
            return cls(
                sandbox_id=sandbox_id,
                envd_version=envd_version,
                envd_access_token=envd_access_token,
                connection_config=connection_config,
                ssh_host=ssh_host,
                ssh_port=ssh_port,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
            )
        else:
            return cls(
                sandbox_id=sandbox_id,
                connection_config=connection_config,
                envd_version=envd_version,
                envd_access_token=envd_access_token,
            )
