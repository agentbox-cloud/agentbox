from typing import Callable, Dict, List, Literal, Optional, Union, overload

import paramiko
import time
from agentbox.connection_config import ConnectionConfig, Username
from agentbox.sandbox.commands.main import ProcessInfo
from agentbox.sandbox.commands.command_handle import CommandResult
from agentbox.sandbox_sync.commands_ssh.command_handle_ssh import SSHSyncCommandHandle, Stderr, Stdout


class SSHCommands:
    """
    Module for executing commands in the sandbox.
    """

    def __init__(
        self,
        ssh_host: str,
        ssh_port: int,
        ssh_username: str,
        ssh_password: str,
        connection_config: ConnectionConfig,
    ) -> None:
        self._ssh_host = ssh_host
        self._ssh_port = ssh_port
        self._ssh_username = ssh_username
        self._ssh_password = ssh_password
        self._connection_config = connection_config
        self._client: Optional[paramiko.SSHClient] = None
        self._processes: Dict[int, SSHSyncCommandHandle] = {}

    def _get_ssh_client(self) -> paramiko.SSHClient:
        if (
            self._client is None
            or not self._client.get_transport()
            or not self._client.get_transport().is_active()
        ):
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._client.connect(
                hostname=self._ssh_host,
                port=self._ssh_port,
                username=self._ssh_username,
                password=self._ssh_password,
                timeout=30,
            )
        return self._client

    def list(self, request_timeout: Optional[float] = None) -> List[ProcessInfo]:
        # ps -eo pid,comm,args --no-headers
        processes = []
        for item in self._processes.values():
            processes.append(ProcessInfo(
                        pid=item.pid,
                        tag=f'ssh-{item.pid}',
                        cmd='',
                        args=[],
                        envs={},
                        cwd="/",
                    ))

        return processes

    def kill(self, pid: int, request_timeout: Optional[float] = None) -> bool:
        handle = self._processes.pop(pid, None)
        if handle:
            # ✅ Removed process {pid}
            return True
        else:
            # ⚠️ No process found for pid {pid}
            return False

    def send_stdin(self, pid: int, data: str, request_timeout: Optional[float] = None):
        if pid in self._processes:
            self._processes[pid].send_stdin(data)
        else:
            raise Exception(f"Process {pid} not found")


    @overload
    def run(
        self,
        cmd: str,
        background: Union[Literal[False], None] = None,
        envs: Optional[Dict[str, str]] = None,
        user: Username = "user",
        cwd: Optional[str] = None,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
        timeout: Optional[float] = 60,
        request_timeout: Optional[float] = None,
    ) -> CommandResult: ...

    @overload
    def run(
        self,
        cmd: str,
        background: Literal[True],
        envs: Optional[Dict[str, str]] = None,
        user: Username = "user",
        cwd: Optional[str] = None,
        on_stdout: None = None,
        on_stderr: None = None,
        timeout: Optional[float] = 60,
        request_timeout: Optional[float] = None,
    ) -> SSHSyncCommandHandle: ...

    def run(
        self,
        cmd: str,
        background: Union[bool, None] = None,
        envs: Optional[Dict[str, str]] = None,
        user: Username = "user",
        cwd: Optional[str] = None,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
        timeout: Optional[float] = 60,
        request_timeout: Optional[float] = None,
    ):
        handle = self._start(cmd, envs, user, cwd, timeout)
        time.sleep(0.5)
        return (
            handle
            if background
            else handle.wait(on_stdout=on_stdout, on_stderr=on_stderr)
        )

    def _start(
        self,
        cmd: str,
        envs: Optional[Dict[str, str]] = None,
        user: Username = "user",
        cwd: Optional[str] = None,
        timeout: Optional[float] = 60,
    ) -> SSHSyncCommandHandle:
        """
        Start command, return handle.
        """
        client = self._get_ssh_client()
        env_str = " ".join([f"{k}={v}" for k, v in envs.items()]) if envs else ""
        full_cmd = f"cd {cwd} && {env_str} {cmd}; echo __CMD_DONE__$?; exit\n" if cwd else f"{env_str} {cmd} ; echo __CMD_DONE__$?; exit\n"

        channel = client.invoke_shell()
        channel.send(full_cmd)

        pid = len(self._processes) + 1000
        handle = SSHSyncCommandHandle(
            pid=pid,
            handle_kill=lambda: self.kill(pid),
            channel=channel,
        )
        self._processes[pid] = handle
        return handle

    def connect(
        self,
        pid: int,
        timeout: Optional[float] = 60,
        request_timeout: Optional[float] = None,
    ) -> SSHSyncCommandHandle:
        """
        Connects to a running command.
        """
        if pid in self._processes:
            return self._processes[pid]
        else:
            raise Exception(f"Process {pid} not found")

# Alias      
Commands = SSHCommands
