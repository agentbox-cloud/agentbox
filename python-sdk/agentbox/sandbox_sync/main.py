import logging
import httpx
import re
import uuid
import json
from datetime import datetime

from typing import Dict, Optional, overload, List, TypedDict, Union

from packaging.version import Version
from typing_extensions import Unpack, Self

from agentbox.api.client.models import InstanceAuthInfo
from agentbox.api.client.types import Unset
from agentbox.connection_config import ConnectionConfig, ApiParams
from agentbox.envd.api import ENVD_API_HEALTH_ROUTE, handle_envd_api_exception
from agentbox.exceptions import SandboxException, format_request_timeout_error
from agentbox.sandbox.main import SandboxSetup
from agentbox.sandbox.sandbox_api import SandboxMetrics
from agentbox.sandbox.utils import class_method_variant
from agentbox.sandbox_sync.adb_shell.adb_shell import ADBShell
from agentbox.sandbox_sync.filesystem.filesystem import Filesystem
from agentbox.sandbox_sync.commands.command import Commands
from agentbox.sandbox_sync.commands.pty import Pty
from agentbox.sandbox_sync.sandbox_api import SandboxApi, SandboxInfo
from agentbox.sandbox_sync.commands_ssh.command_ssh import SSHCommands
from agentbox.sandbox_sync.filesystem_ssh.filesystem_ssh import SSHSyncFilesystem
from agentbox.sandbox_sync.commands_ssh2.command_ssh2 import SSHCommands2

logger = logging.getLogger(__name__)


class TransportWithLogger(httpx.HTTPTransport):
    def handle_request(self, request):
        url = f"{request.url.scheme}://{request.url.host}{request.url.path}"
        logger.info(f"Request: {request.method} {url}")
        response = super().handle_request(request)

        # data = connect.GzipCompressor.decompress(response.read()).decode()
        logger.info(f"Response: {response.status_code} {url}")

        return response

    @property
    def pool(self):
        return self._pool


class SandboxOpts(TypedDict, total=False):
    sandbox_id: str
    envd_version: Optional[str]
    envd_access_token: Optional[str]
    connection_config: ConnectionConfig
    # optional fields
    ssh_host: Optional[str]
    ssh_port: Optional[int]
    ssh_username: Optional[str]
    ssh_password: Optional[str]


class Sandbox(SandboxSetup, SandboxApi):
    """
    Agentbox sandbox is a secure and isolated cloud environment.

    The sandbox allows you to:
    - Access Linux OS and Android OS
    - Create, list, and delete files and directories
    - Run commands
    - Run isolated code
    - Access the internet

    Check docs [here](https://agentbox.cloud/docs).

    Use the `Sandbox()` to create a new sandbox.

    Example:
    ```python
    from agentbox import Sandbox

    sandbox = Sandbox()
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
    def adb_shell(self) -> ADBShell:
        """
        Module for adb shell in the sandbox.
        """
        return self._adb_shell

    @property
    def pty(self) -> Pty:
        """
        Module for interacting with the sandbox pseudo-terminal.
        """
        return self._pty

    @property
    def sandbox_id(self) -> str:
        """
        Unique identifier of the sandbox
        """
        return self._sandbox_id

    @property
    def envd_api_url(self) -> str:
        return self._envd_api_url

    @property
    def _envd_access_token(self) -> str:
        """Private property to access the envd token"""
        return self.__envd_access_token

    @_envd_access_token.setter
    def _envd_access_token(self, value: Optional[str]):
        """Private setter for envd token"""
        self.__envd_access_token = value

    @property
    def connection_config(self) -> ConnectionConfig:
        return self._connection_config

    def __init__(
        self,
        template: Optional[str] = None,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None,
        envs: Optional[Dict[str, str]] = None,
        secure: Optional[bool] = None,
        **opts: Unpack[Union[SandboxOpts, ApiParams]],
    ):
        """
        Create a new sandbox.

        By default, the sandbox is created from the default `base` sandbox template.

        :param template: Sandbox template name or ID
        :param timeout: Timeout for the sandbox in **seconds**, default to 300 seconds. Maximum time a sandbox can be kept alive is 24 hours (86_400 seconds) for Pro users and 1 hour (3_600 seconds) for Hobby users
        :param metadata: Custom metadata for the sandbox
        :param envs: Custom environment variables for the sandbox
        :param secure: Envd is secured with access token and cannot be used without it, defaults to `True`.
        :param sandbox_id: Sandbox ID (for connecting to existing sandbox, passed via opts)
        :param connection_config: Connection configuration (passed via opts)
        :param envd_version: Envd version (passed via opts)
        :param envd_access_token: Envd access token (passed via opts)
        :param ssh_host: SSH host (passed via opts, for brd type sandboxes)
        :param ssh_port: SSH port (passed via opts, for brd type sandboxes)
        :param ssh_username: SSH username (passed via opts, for brd type sandboxes)
        :param ssh_password: SSH password (passed via opts, for brd type sandboxes)
        :param api_key: AGENTBOX API Key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable (passed via opts)
        :param domain: Domain of the sandbox server (passed via opts)
        :param debug: Enable debug mode (passed via opts)
        :param request_timeout: Timeout for the request in **seconds** (passed via opts)
        :param proxy: Proxy to use for the request and for the **requests made to the returned sandbox** (passed via opts)

        :return: sandbox instance for the new sandbox
        """
        super().__init__()

        # Extract and validate initialization parameters from opts
        sandbox_id = opts.get("sandbox_id")
        connection_config = opts.get("connection_config")
        
        if sandbox_id and (metadata is not None or template is not None):
            raise SandboxException(
                "Cannot set metadata or timeout when connecting to an existing sandbox. "
                "Use Sandbox.connect method instead.",
            )

        # Initialize connection config
        self._connection_config = connection_config if connection_config is not None else ConnectionConfig(**opts)
        
        # Initialize all private attributes with default values or from opts
        self._envd_version = None
        self._envd_access_token = None
        self._ssh_host = None
        self._ssh_port = None
        self._ssh_username = None
        self._ssh_password = None
        
        # Set attributes from opts if provided
        envd_version = opts.get("envd_version")
        if envd_version is not None:
            self._envd_version = Version(envd_version) if isinstance(envd_version, str) else envd_version
        
        envd_access_token = opts.get("envd_access_token")
        if envd_access_token is not None:
            self._envd_access_token = envd_access_token
        
        ssh_host = opts.get("ssh_host")
        if ssh_host is not None:
            self._ssh_host = ssh_host
        
        ssh_port = opts.get("ssh_port")
        if ssh_port is not None:
            self._ssh_port = ssh_port
        
        ssh_username = opts.get("ssh_username")
        if ssh_username is not None:
            self._ssh_username = ssh_username
        
        ssh_password = opts.get("ssh_password")
        if ssh_password is not None:
            self._ssh_password = ssh_password
        if self._connection_config.debug:
            self._sandbox_id = "debug_sandbox_id"
            self._envd_version = None
            self._envd_access_token = None
            self._ssh_host = "127.0.0.1"
            self._ssh_port = 22
            self._ssh_username = "debug"
            self._ssh_password = "debug"
            # self._adb_info = SandboxADB(
            #     adb_auth_command="adb shell",
            #     auth_password="debug",
            #     connect_command="adb connect 127.0.0.1",
            #     expire_time="",
            #     forwarder_command="",
            #     instance_no="debug_sandbox_id"
            # )
        elif sandbox_id is not None:
            response = SandboxApi._cls_get_info(
                sandbox_id=sandbox_id,
                **self._connection_config.get_api_params(),
            )

            self._sandbox_id = sandbox_id
            if self._envd_version is None:
                self._envd_version = Version(response.envd_version) if response.envd_version else None
            if self._envd_access_token is None:
                self._envd_access_token = response._envd_access_token

            if response._envd_access_token is not None and not isinstance(
                    response._envd_access_token, Unset
            ):
                self._connection_config.headers["X-Access-Token"] = response._envd_access_token

        else:
            template = template or self.default_template
            timeout = timeout or self.default_sandbox_timeout
            response = SandboxApi._create_sandbox(
                template=template,
                timeout=timeout,
                auto_pause=False,
                metadata=metadata,
                env_vars=envs,
                secure=secure or False,
                **opts,
            )
            self._sandbox_id = response.sandbox_id
            if self._envd_version is None:
                self._envd_version = Version(response.envd_version) if response.envd_version else None

            if response.envd_access_token is not None and not isinstance(
                response.envd_access_token, Unset
            ):
                if self._envd_access_token is None:
                    self._envd_access_token = response.envd_access_token
                self._connection_config.headers["X-Access-Token"] = response.envd_access_token
            else:
                if self._envd_access_token is None:
                    self._envd_access_token = None

        self._transport = TransportWithLogger(limits=self._limits, proxy=self._connection_config.proxy)

        # 根据 sandbox id 进行区分 commands 类型
        if "brd" in self._sandbox_id.lower():
            # ssh info
            ssh_info = SandboxApi._get_ssh(
                sandbox_id=self._sandbox_id,
                **self._connection_config.get_api_params(),
            )
            # print("ssh_info:", ssh_info)
            # Parse SSH connection details from the connect command
            pattern = r'ssh\s+-p\s+(\d+).*?\s+([^@\s]+)@([\w\.-]+)'
            ssh_match = re.search(pattern, ssh_info.connect_command)
            if ssh_match:
                self._ssh_port = int(ssh_match.group(1))
                self._ssh_username = ssh_match.group(2)
                self._ssh_host = ssh_match.group(3)
                self._ssh_password = ssh_info.auth_password
            else:
                raise Exception("Could not parse SSH connection details")
            # Get adb connection details
            # self._adb_info = SandboxApi._get_adb(
            #     sandbox_id=self._sandbox_id,
            #     api_key=api_key,
            #     domain=domain,
            #     debug=debug,
            #     proxy=proxy,
            # )
            # self._watch_commands = SSHCommands(
            #     self._ssh_host,
            #     self._ssh_port,
            #     self._ssh_username,
            #     self._ssh_password,
            #     self.connection_config,
            # )
            # self._commands = SSHCommands(
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
            self._commands = SSHCommands2(
                self._ssh_host,
                self._ssh_port,
                self._ssh_username,
                self._ssh_password,
                self.connection_config,
            )
            self._filesystem = SSHSyncFilesystem(
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
            self._envd_api_url = f"{'http' if self.connection_config.debug else 'https'}://{self.get_host(self.envd_port)}"
            self._envd_api = httpx.Client(
                base_url=self.envd_api_url,
                transport=self._transport,
                headers=self.connection_config.headers,
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

    def is_running(self, request_timeout: Optional[float] = None) -> bool:
        """
        Check if the sandbox is running.

        :param request_timeout: Timeout for the request in **seconds**

        :return: `True` if the sandbox is running, `False` otherwise

        Example
        ```python
        sandbox = Sandbox()
        sandbox.is_running() # Returns True

        sandbox.kill()
        sandbox.is_running() # Returns False
        ```
        """
        # For brd type sandboxes, _envd_api is not initialized
        if not hasattr(self, '_envd_api') or self._envd_api is None:
            # For SSH-based sandboxes, we assume they are running if we can connect
            # This is a simplified check - in practice you might want to verify SSH connection
            return True
        
        try:
            r = self._envd_api.get(
                ENVD_API_HEALTH_ROUTE,
                timeout=self.connection_config.get_request_timeout(request_timeout),
            )

            if r.status_code == 502:
                return False

            err = handle_envd_api_exception(r)

            if err:
                raise err

        except httpx.TimeoutException:
            raise format_request_timeout_error()

        return True

    @overload
    def connect(
        self,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ):
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

    @overload
    @classmethod
    def connect(
        cls,
        sandbox_id: str,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ):
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
        ...

    @class_method_variant("_cls_connect")
    def connect(
        self,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ):
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
        return self.__class__._cls_connect(
            sandbox_id=self.sandbox_id,
            timeout=timeout,
            **self._connection_config.get_api_params(**opts),
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.kill()

    @overload
    def kill(self, request_timeout: Optional[float] = None) -> bool:
        """
        Kill the sandbox.

        :param request_timeout: Timeout for the request in **seconds**

        :return: `True` if the sandbox was killed, `False` if the sandbox was not found
        """
        ...

    @overload
    @staticmethod
    def kill(
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
    def kill(self, **opts: Unpack[ApiParams]) -> bool:
        """
        Kill the sandbox.

        :param request_timeout: Timeout for the request
        :return: `True` if the sandbox was killed, `False` if the sandbox was not found
        """
        return SandboxApi._cls_kill(
            sandbox_id=self.sandbox_id,
            **self._connection_config.get_api_params(**opts),
        )

    @overload
    def set_timeout(
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
    def set_timeout(
        sandbox_id: str,
        timeout: int,
        **opts: Unpack[ApiParams],
    ) -> None:
        """
        Set the timeout of the sandbox specified by sandbox ID.
        After the timeout expires the sandbox will be automatically killed.
        This method can extend or reduce the sandbox timeout set when creating the sandbox or from the last call to `.set_timeout`.

        Maximum time a sandbox can be kept alive is 24 hours (86_400 seconds) for Pro users and 1 hour (3_600 seconds) for Hobby users.

        :param sandbox_id: Sandbox ID
        :param timeout: Timeout for the sandbox in **seconds**
        :param api_key: E2B API Key to use for authentication, defaults to `AGENTBOX_API_KEY` environment variable
        :param request_timeout: Timeout for the request in **seconds**
        :param proxy: Proxy to use for the request
        """
        ...

    @class_method_variant("_cls_set_timeout")
    def set_timeout(
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
        SandboxApi._cls_set_timeout(
            sandbox_id=self.sandbox_id,
            timeout=timeout,
            **self._connection_config.get_api_params(**opts),
        )

    @overload
    def get_info(
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
    def get_info(
        sandbox_id: str,
        **opts: Unpack[ApiParams],
    ) -> SandboxInfo:
        """
        Get sandbox information like sandbox ID, template, metadata, started at/end at date.

        :return: Sandbox info
        """
        ...

    @class_method_variant("_cls_get_info")
    def get_info(
        self,
        **opts: Unpack[ApiParams],
    ) -> SandboxInfo:
        """
        Get sandbox information like sandbox ID, template, metadata, started at/end at date.

        :return: Sandbox info
        """
        return SandboxApi._cls_get_info(
            sandbox_id=self.sandbox_id,
            **self._connection_config.get_api_params(**opts),
        )

    @overload
    def get_metrics(
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
    def get_metrics(
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
    def get_metrics(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        **opts: Unpack[ApiParams],
    ) -> List[SandboxMetrics]:
        """
        Get the metrics of the sandbox specified by sandbox ID.

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

        return SandboxApi._cls_get_metrics(
            sandbox_id=self.sandbox_id,
            start=start,
            end=end,
            **self._connection_config.get_api_params(**opts),
        )

    def get_instance_no(
        self,
        **opts: Unpack[ApiParams],
    ) -> str:
        """
        Get sandbox instance number.
        :param request_timeout: Timeout for the request in **seconds**
        :return: Sandbox instance number
        """
        return SandboxApi.get_instance_no(
            sandbox_id=self.sandbox_id,
            **self._connection_config.get_api_params(**opts),
        )
    
    def get_instance_auth_info(
        self,
        valid_time: Optional[int] = 3600,
        **opts: Unpack[ApiParams],
    ) -> InstanceAuthInfo:
        """
        Get sandbox instance auth info.
        :param request_timeout: Timeout for the request in **seconds**
        :return: Sandbox instance auth info
        """
        return SandboxApi.get_instance_auth_info(
            sandbox_id=self.sandbox_id,
            valid_time=valid_time,
            **self._connection_config.get_api_params(**opts),
        )

    @classmethod
    def beta_create(
        cls,
        template: Optional[str] = None,
        timeout: Optional[int] = None,
        auto_pause: bool = False,
        metadata: Optional[Dict[str, str]] = None,
        envs: Optional[Dict[str, str]] = None,
        secure: Optional[bool] = None,
        **opts: Unpack[ApiParams],
    ):
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

        sandbox = cls._create(
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
    def _create(
        cls,
        template: Optional[str],
        timeout: Optional[int],
        auto_pause: bool,
        metadata: Optional[Dict[str, str]],
        envs: Optional[Dict[str, str]],
        secure: bool,
        **opts: Unpack[ApiParams],
    ):
        extra_sandbox_headers = {}

        if opts.get("debug"):
            sandbox_id = "debug_sandbox_id"
            envd_version = None
            envd_access_token = None
        else:
            response = SandboxApi._create_sandbox(
                template=template or cls.default_template,
                timeout=timeout or cls.default_sandbox_timeout,
                auto_pause=auto_pause,
                metadata=metadata,
                env_vars=envs,
                secure=secure,
                **opts,
            )

            sandbox_id = response.sandbox_id
            envd_version = Version(response.envd_version)
            envd_access_token = response.envd_access_token

            if envd_access_token is not None and not isinstance(envd_access_token, Unset):
                extra_sandbox_headers["X-Access-Token"] = envd_access_token
        
        connection_config = ConnectionConfig(
            extra_sandbox_headers=extra_sandbox_headers,
            **opts,
        )

        if "brd" in sandbox_id.lower():
            # Get SSH connection details
            ssh_info = SandboxApi._get_ssh(
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
                connection_config=connection_config,
                envd_version=envd_version,
                envd_access_token=envd_access_token,
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

    @classmethod
    def _cls_connect(
        cls,
        sandbox_id: str,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ):
        # Skip resume operation for "brd" sandboxes
        if "brd" in sandbox_id.lower():
            sandbox_info = SandboxApi._cls_get_info(
                sandbox_id=sandbox_id,
                **opts,
            )

            connection_config = ConnectionConfig(**opts)

            # Get SSH connection details
            ssh_info = SandboxApi._get_ssh(
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
            sandbox = SandboxApi._cls_connect(
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
    def resume(self, 
        auto_pause: bool = False, 
        timeout: Optional[int] = None, 
        **opts: Unpack[ApiParams]
        ):
        ...

    @overload
    @classmethod
    def resume(
        cls,
        sandbox_id: str,
        auto_pause: bool = False,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ):
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

        :return: A running sandbox instance
        """
        ...
    
    @class_method_variant("_cls_resume")
    def resume(
        self,
        auto_pause: bool = False,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ):
        """
        Resume the sandbox.

        The **default sandbox timeout of 300 seconds** will be used for the resumed sandbox.
        If you pass a custom timeout via the `timeout` parameter, it will be used instead.

        :param auto_pause: Automatically pause the sandbox after the timeout expires. Defaults to `False`.
        :param timeout: Timeout for the sandbox in **seconds**
        :param request_timeout: Timeout for the request in **seconds**

        :return: A running sandbox instance
        """
        return self.__class__._cls_resume(
            sandbox_id=self.sandbox_id,
            auto_pause=auto_pause,
            timeout=timeout,
            **self._connection_config.get_api_params(**opts),
        )
    
    @classmethod
    def _cls_resume(
        cls,
        sandbox_id: str,
        auto_pause: bool = False,
        timeout: Optional[int] = None,
        **opts: Unpack[ApiParams],
    ):
        # Skip resume operation for "brd" sandboxes
        if "brd" in sandbox_id.lower():
            sandbox_info = SandboxApi._cls_get_info(
                sandbox_id=sandbox_id,
                **opts,
            )

            connection_config = ConnectionConfig(**opts)

            # Get SSH connection details
            ssh_info = SandboxApi._get_ssh(
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
            sandbox = SandboxApi._cls_resume(
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
    def pause(
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
    def pause(
        sandbox_id: str,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        debug: Optional[bool] = None,
        request_timeout: Optional[float] = None,
    ) -> str:
        """
        Pause a sandbox by its ID.

        :param sandbox_id: Sandbox ID
        :param api_key: E2B API Key to use for authentication
        :param domain: Domain of the sandbox server
        :param debug: Enable debug mode
        :param request_timeout: Timeout for the request in **seconds**

        :return: sandbox ID that can be used to resume the sandbox
        """
        ...

    @class_method_variant("_cls_pause")
    def pause(
        self,
        **opts: Unpack[ApiParams],
    ) -> bool:
        """
        Pause the sandbox.

        :param request_timeout: Timeout for the request in **seconds**

        :return: sandbox ID that can be used to resume the sandbox
        """
        return SandboxApi._cls_pause(
            sandbox_id=self.sandbox_id,
            **self._connection_config.get_api_params(**opts),
        )