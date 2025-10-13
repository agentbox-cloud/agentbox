import asyncio
import paramiko

from functools import partial
from typing import Dict, List, Literal, Optional, Union, overload

from agentbox.connection_config import (
    ConnectionConfig,
    Username,
)
from agentbox.sandbox.commands.main import ProcessInfo
from agentbox.sandbox.commands.command_handle import CommandResult
from agentbox.sandbox_async.commands_ssh.command_handle_ssh import SSHAsyncCommandHandle, Stderr, Stdout
from agentbox.sandbox_async.utils import OutputHandler


class SSHCommands:
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
        self._client = None
        self._processes = {}

    async def _get_ssh_client(self):
        if self._client is None or not self._client.get_transport() or not self._client.get_transport().is_active():
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            connect_func = partial(
                self._client.connect,
                hostname=self._ssh_host,
                port=self._ssh_port,
                username=self._ssh_username,
                password=self._ssh_password,
                timeout=60,
            )
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, connect_func)
            except Exception as e:
                print("SSH 连接失败：", e)
                raise
        return self._client

    async def list(self, request_timeout: Optional[float] = None) -> List[ProcessInfo]:
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

    async def kill(self, pid: int, request_timeout: Optional[float] = None) -> bool:
        handle = self._processes.pop(pid, None)
        if handle:
            # ✅ Removed process {pid}
            return True
        else:
            # ⚠️ No process found for pid {pid}
            return False

    async def send_stdin(self, pid: int, data: str, request_timeout: Optional[float] = None) -> None:
        if pid in self._processes:
            await self._processes[pid].send_stdin(data)
        else:
            raise Exception(f"Process {pid} not found")

    async def run(
        self,
        cmd: str,
        background: Union[bool, None] = None,
        envs: Optional[Dict[str, str]] = None,
        user: Username = "user",
        cwd: Optional[str] = None,
        on_stdout: Optional[OutputHandler[Stdout]] = None,
        on_stderr: Optional[OutputHandler[Stderr]] = None,
        timeout: Optional[float] = 60,
        request_timeout: Optional[float] = None,
    ):
        proc = await self._start(cmd, envs, user, cwd, timeout, request_timeout, on_stdout, on_stderr)
        return proc if background else await proc.wait()

    async def _start(
        self,
        cmd: str,
        envs: Optional[Dict[str, str]] = None,
        user: Username = "user",
        cwd: Optional[str] = None,
        timeout: Optional[float] = 60,
        request_timeout: Optional[float] = None,
        on_stdout: Optional[OutputHandler[Stdout]] = None,
        on_stderr: Optional[OutputHandler[Stderr]] = None,
    ) -> SSHAsyncCommandHandle:
        client = await self._get_ssh_client()
        env_str = " ".join([f"{k}={v}" for k, v in envs.items()]) + " " if envs else ""
        full_cmd = f"cd {cwd} && {env_str}{cmd}; echo __CMD_DONE__$?; exit\n" if cwd else f"{env_str}{cmd} ; echo __CMD_DONE__$?; exit\n"
        # full_cmd = f"cd {cwd} && {env_str}{cmd}\n" if cwd else f"{env_str}{cmd}\n"
        channel = client.invoke_shell()
        channel.send(full_cmd)

        pid = len(self._processes) + 1000
        handle = SSHAsyncCommandHandle(
            pid=pid,
            handle_kill=lambda: self.kill(pid),
            channel=channel,
            on_stdout=on_stdout,
            on_stderr=on_stderr,
        )
        self._processes[pid] = handle
        return handle

    async def connect(
        self,
        pid: int,
        timeout: Optional[float] = 60,
        request_timeout: Optional[float] = None,
        on_stdout: Optional[OutputHandler[Stdout]] = None,
        on_stderr: Optional[OutputHandler[Stderr]] = None,
    ) -> SSHAsyncCommandHandle:
        if pid in self._processes:
            return self._processes[pid]
        raise Exception(f"Process {pid} not found")


Commands = SSHCommands
