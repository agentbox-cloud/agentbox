import logging
import httpx
import re

from typing import Dict, Optional, TypedDict, overload
from typing_extensions import Unpack, Self

from agentbox.api.client.types import Unset
from agentbox.connection_config import ConnectionConfig, ProxyTypes
from agentbox.envd.api import ENVD_API_HEALTH_ROUTE, ahandle_envd_api_exception
from agentbox.exceptions import format_request_timeout_error
from agentbox.sandbox.main import SandboxSetup
from agentbox.sandbox.utils import class_method_variant
from agentbox.sandbox_async.adb_shell.adb_shell import ADBShell
from agentbox.sandbox_async.filesystem.filesystem import Filesystem
from agentbox.sandbox_async.commands.command import Commands
from agentbox.sandbox_async.commands.pty import Pty
from agentbox.sandbox_async.sandbox_api import SandboxApi, SandboxInfo
from agentbox.api.client.models import SandboxADB, InstanceAuthInfo
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
        self._envd_version = opts.get("envd_version")
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
                self._envd_version,
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
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        proxy: Optional[ProxyTypes] = None,
        secure: Optional[bool] = None,
        auto_pause: bool = False,
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

        connection_headers = {}

        if debug:
            sandbox_id = "debug_sandbox_id"
            envd_version = None
            envd_access_token = None
            ssh_host = "127.0.0.1"
            ssh_port = 22
            ssh_username = "debug"
            ssh_password = "debug"
            adb_info = SandboxADB(
                adb_auth_command="adb shell",
                auth_password="debug",
                connect_command="adb connect 127.0.0.1",
                expire_time="",
                forwarder_command="",
                instance_no="debug_sandbox_id"
            )
        else:
            response = await SandboxApi._create_sandbox(
                template=template or cls.default_template,
                api_key=api_key,
                timeout=timeout or cls.default_sandbox_timeout,
                metadata=metadata,
                domain=domain,
                debug=debug,
                request_timeout=request_timeout,
                env_vars=envs,
                secure=secure,
                proxy=proxy,
                auto_pause=auto_pause,
            )

            sandbox_id = response.sandbox_id
            envd_version = response.envd_version
            envd_access_token = response.envd_access_token

            if envd_access_token is not None and not isinstance(
                envd_access_token, Unset
            ):
                connection_headers["X-Access-Token"] = envd_access_token

        connection_config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            headers=connection_headers,
            proxy=proxy,
        )

        if "brd" in sandbox_id.lower():
            # Get SSH connection details
            ssh_info = await SandboxApi._get_ssh(
                sandbox_id=sandbox_id,
                api_key=api_key,
                domain=domain,
                debug=debug,
                request_timeout=request_timeout,
                proxy=proxy,
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
            # Get adb connection details
            adb_info = await SandboxApi._get_adb(
                sandbox_id=sandbox_id,
                api_key=api_key,
                domain=domain,
                debug=debug,
                proxy=proxy,
            )
            return cls(
                sandbox_id=sandbox_id,
                envd_version=envd_version,
                envd_access_token=envd_access_token,
                connection_config=connection_config,
                ssh_host=ssh_host,
                ssh_port=ssh_port,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
                adb_auth_command=adb_info.adb_auth_command,
                adb_auth_password=adb_info.auth_password,
                adb_connect_command=adb_info.connect_command,
                adb_forwarder_command=adb_info.forwarder_command
            )
        else:
            return cls(
                sandbox_id=sandbox_id,
                envd_version=envd_version,
                envd_access_token=envd_access_token,
                connection_config=connection_config,
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.kill()

    @overload
    async def kill(self, request_timeout: Optional[float] = None) -> bool:
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
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        proxy: Optional[ProxyTypes] = None,
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
        request_timeout: Optional[float] = None,
    ) -> bool:  # type: ignore
        config_dict = self.connection_config.__dict__
        config_dict.pop("access_token", None)
        config_dict.pop("api_url", None)

        if request_timeout:
            config_dict["request_timeout"] = request_timeout

        return await SandboxApi._cls_kill(
            sandbox_id=self.sandbox_id,
            **config_dict,
        )

    @overload
    async def set_timeout(
        self,
        timeout: int,
        request_timeout: Optional[float] = None,
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
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        proxy: Optional[ProxyTypes] = None,
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
    async def set_timeout(  # type: ignore
        self,
        timeout: int,
        request_timeout: Optional[float] = None,
    ) -> None:
        config_dict = self.connection_config.__dict__
        config_dict.pop("access_token", None)
        config_dict.pop("api_url", None)

        if request_timeout:
            config_dict["request_timeout"] = request_timeout

        await SandboxApi._cls_set_timeout(
            sandbox_id=self.sandbox_id,
            timeout=timeout,
            **config_dict,
        )

    @classmethod
    async def resume(
        cls,
        sandbox_id: str,
        timeout: Optional[int] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
    ) -> Self:
        """
        Resume the sandbox.

        The **default sandbox timeout of 300 seconds** will be used for the resumed sandbox.
        If you pass a custom timeout via the `timeout` parameter, it will be used instead.

        :param sandbox_id: sandbox ID
        :param timeout: Timeout for the sandbox in **seconds**
        :param api_key: E2B API Key to use for authentication
        :param domain: Domain of the sandbox server
        :param debug: Enable debug mode
        :param request_timeout: Timeout for the request in **seconds**

        :return: A running sandbox instance
        """

        timeout = timeout or cls.default_sandbox_timeout

        await SandboxApi._cls_resume(
            sandbox_id=sandbox_id,
            request_timeout=request_timeout,
            timeout=timeout,
            api_key=api_key,
            domain=domain,
            debug=debug,
        )

        connection_headers = {}
        response = await SandboxApi.get_info(sandbox_id=sandbox_id, api_key=api_key, domain=domain, debug=debug)
        if response._envd_access_token is not None and not isinstance(
            response._envd_access_token, Unset
        ):
            connection_headers["X-Access-Token"] = response._envd_access_token

        connection_config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            headers=connection_headers,
        )

        if "brd" in sandbox_id.lower():
            # Get SSH connection details
            ssh_info = await SandboxApi._get_ssh(
                sandbox_id=sandbox_id,
                api_key=api_key,
                domain=domain,
                debug=debug,
                request_timeout=request_timeout,
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
            # Get adb connection details
            adb_info = await SandboxApi._get_adb(
                sandbox_id=sandbox_id,
                api_key=api_key,
                domain=domain,
                debug=debug,
            )
            return cls(
                sandbox_id=sandbox_id,
                envd_version=response.envd_version,
                envd_access_token=response._envd_access_token,
                connection_config=connection_config,
                ssh_host=ssh_host,
                ssh_port=ssh_port,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
                adb_auth_command=adb_info.adb_auth_command,
                adb_auth_password=adb_info.auth_password,
                adb_connect_command=adb_info.connect_command,
                adb_forwarder_command=adb_info.forwarder_command
            )
        else:
            return cls(
                sandbox_id=sandbox_id,
                envd_version=response.envd_version,
                envd_access_token=response._envd_access_token,
                connection_config=connection_config,
                commands=cls.commands
            )

    @overload
    async def pause(
        self,
        request_timeout: Optional[float] = None,
    ) -> str:
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
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
    ) -> str:
        """
        Pause the sandbox specified by sandbox ID.

        :param sandbox_id: Sandbox ID
        :param api_key: E2B API Key to use for authentication, defaults to `E2B_API_KEY` environment variable
        :param request_timeout: Timeout for the request in **seconds**

        :return: sandbox ID that can be used to resume the sandbox
        """
        ...

    @class_method_variant("_cls_pause")
    async def pause(  # type: ignore
        self,
        request_timeout: Optional[float] = None,
    ) -> str:
        """
        Pause the sandbox.

        :param request_timeout: Timeout for the request in **seconds**

        :return: sandbox ID that can be used to resume the sandbox
        """

        await SandboxApi._cls_pause(
            sandbox_id=self.sandbox_id,
            api_key=self.connection_config.api_key,
            domain=self.connection_config.domain,
            debug=self.connection_config.debug,
            request_timeout=request_timeout,
        )

        return self.sandbox_id

    async def get_info(  # type: ignore
        self,
        request_timeout: Optional[float] = None,
    ) -> SandboxInfo:
        """
        Get sandbox information like sandbox ID, template, metadata, started at/end at date.
        :param request_timeout: Timeout for the request in **seconds**
        :return: Sandbox info
        """

        config_dict = self.connection_config.__dict__
        config_dict.pop("access_token", None)
        config_dict.pop("api_url", None)

        if request_timeout:
            config_dict["request_timeout"] = request_timeout

        return await SandboxApi.get_info(
            sandbox_id=self.sandbox_id,
            **config_dict,
        )

    async def get_instance_no(  # type: ignore
        self,
        request_timeout: Optional[float] = None,
    ) -> str:
        """
        Get sandbox instance number.
        :param request_timeout: Timeout for the request in **seconds**
        :return: Sandbox instance number
        """
        config_dict = self.connection_config.__dict__
        config_dict.pop("access_token", None)
        config_dict.pop("api_url", None)

        if request_timeout:
            config_dict["request_timeout"] = request_timeout

        return await SandboxApi.get_instance_no(
            sandbox_id=self.sandbox_id,
            **config_dict,
        )
    
    async def get_instance_auth_info(  # type: ignore
        self,
        valid_time: Optional[int] = None,
        request_timeout: Optional[float] = None,
    ) -> InstanceAuthInfo:
        """
        Get sandbox instance auth info.
        :param request_timeout: Timeout for the request in **seconds**
        :return: Sandbox instance auth info
        """
        config_dict = self.connection_config.__dict__
        config_dict.pop("access_token", None)
        config_dict.pop("api_url", None)

        if request_timeout:
            config_dict["request_timeout"] = request_timeout

        return await SandboxApi.get_instance_auth_info(
            sandbox_id=self.sandbox_id,
            valid_time=valid_time,
            **config_dict,
        )

    @overload
    async def connect(
        self,
        timeout: Optional[int] = None,
        request_timeout: Optional[float] = None,
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
        sandbox = Sandbox()
        sandbox.pause()

        # Another code block
        same_sandbox = sandbox.connect()
        ```
        """
        ...

    @classmethod
    async def connect(
        cls,
        sandbox_id: str,
        timeout: Optional[int] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> Self:
        """
        Connect to a sandbox. If the sandbox is paused, it will be automatically resumed.
        Sandbox must be either running or be paused.

        With sandbox ID you can connect to the same sandbox from different places or environments (serverless functions, etc).

        :param sandbox_id: Sandbox ID
        :param timeout: Timeout for the sandbox in **seconds**.
            For running sandboxes, the timeout will update only if the new timeout is longer than the existing one.
        :param api_key: AGENTBOX API Key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param domain: AGENTBOX domain to use for authentication, defaults to `AGENTBOX_DOMAIN` environment variable
        :param debug: Enable debug mode
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request and for the **requests made to the returned sandbox**
        :return: A running sandbox instance

        @example
        ```python
        sandbox = Sandbox()
        Sandbox.pause(sandbox.sandbox_id)

        # Another code block
        same_sandbox = Sandbox.connect(sandbox.sandbox_id)
        ```
        """
        return await cls._cls_connect(
            sandbox_id=sandbox_id,
            timeout=timeout,
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            proxy=proxy,
        )

    @class_method_variant("_cls_connect")
    async def connect(
        self,
        timeout: Optional[int] = None,
        request_timeout: Optional[float] = None,
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
        sandbox = Sandbox()
        sandbox.pause()

        # Another code block
        same_sandbox = sandbox.connect()
        ```
        """
        config_dict = self.connection_config.__dict__
        config_dict.pop("access_token", None)
        config_dict.pop("api_url", None)
        config_dict.pop("headers", None)

        if request_timeout:
            config_dict["request_timeout"] = request_timeout

        return await self.__class__._cls_connect(
            sandbox_id=self.sandbox_id,
            timeout=timeout,
            **config_dict,
        )

    @classmethod
    async def _cls_connect(
        cls,
        sandbox_id: str,
        timeout: Optional[int] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        proxy: Optional[ProxyTypes] = None,
    ) -> Self:

        connection_config = ConnectionConfig(
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            proxy=proxy,
        )
        if "brd" in sandbox_id.lower():
            ssh_info = await SandboxApi._get_ssh(
                sandbox_id=sandbox_id,
                api_key=api_key,
                domain=domain,
                debug=debug,
                request_timeout=request_timeout,
                proxy=proxy,
            )
            pattern = r'ssh\s+-p\s+(\d+).*?\s+([^@\s]+)@([\w\.-]+)'
            ssh_match = re.search(pattern, ssh_info.connect_command)
            if ssh_match:
                ssh_port = int(ssh_match.group(1))
                ssh_username = ssh_match.group(2)
                ssh_host = ssh_match.group(3)
                ssh_password = ssh_info.auth_password
            else:
                raise Exception("Could not parse SSH connection details")
            adb_info = await SandboxApi._get_adb(
                sandbox_id=sandbox_id,
                api_key=api_key,
                domain=domain,
                debug=debug,
                request_timeout=request_timeout,
                proxy=proxy,
            )
            return cls(
                sandbox_id=sandbox_id,
                connection_config=connection_config,
                ssh_host=ssh_host,
                ssh_port=ssh_port,
                ssh_username=ssh_username,
                ssh_password=ssh_password,
                adb_auth_command=adb_info.adb_auth_command,
                adb_auth_password=adb_info.auth_password,
                adb_connect_command=adb_info.connect_command,
                adb_forwarder_command=adb_info.forwarder_command
            )
        else:
            timeout = timeout or cls.default_connect_timeout
            await SandboxApi._cls_connect(
                sandbox_id=sandbox_id,
                timeout=timeout,
                api_key=api_key,
                domain=domain,
                debug=debug,
                request_timeout=request_timeout,
            )

            connection_headers = {}
            response = await SandboxApi.get_info(
                sandbox_id=sandbox_id,
                api_key=api_key,
                domain=domain,
                debug=debug,
                request_timeout=request_timeout,
            )
            envd_access_token = response._envd_access_token
            if envd_access_token is not None and not isinstance(envd_access_token, Unset):
                connection_headers["X-Access-Token"] = envd_access_token
            connection_config.headers = connection_headers
            return cls(
                sandbox_id=sandbox_id,
                envd_version=response.envd_version,
                envd_access_token=envd_access_token,
                connection_config=connection_config,
            )
    
    @classmethod
    async def beta_create(
        cls,
        template: Optional[str] = None,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None,
        envs: Optional[Dict[str, str]] = None,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
        proxy: Optional[ProxyTypes] = None,
        secure: Optional[bool] = None,
        auto_pause: bool = False,
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
        return await cls.create(
            template=template or cls.default_template,
            timeout=timeout or cls.default_sandbox_timeout,
            metadata=metadata,
            envs=envs,
            api_key=api_key,
            domain=domain,
            debug=debug,
            request_timeout=request_timeout,
            proxy=proxy,
            secure=secure,
            auto_pause=auto_pause,
        )

    async def set_model_information(
        self,
        model: str,
        brand: str,
        manufacturer: str,
        request_timeout: Optional[float] = None,
    ) -> None:
        """
        Set model information for the sandbox.
        """

        return await SandboxApi._cls_set_model_information(
            sandbox_id=self.sandbox_id,
            model=model,
            brand=brand,
            manufacturer=manufacturer,
            request_timeout=request_timeout,
            api_key=self.connection_config.api_key,
            domain=self.connection_config.domain,
            debug=self.connection_config.debug,
            proxy=self.connection_config.proxy,
            headers=self.connection_config.headers,
        )