import asyncio
import paramiko

from functools import partial
from typing import Dict, List, Optional, Union

from agentbox.connection_config import (
    ConnectionConfig,
    Username,
)
from agentbox.sandbox.commands.main import ProcessInfo
from agentbox.sandbox_async.commands_ssh2.command_handle_ssh2 import SSHAsyncCommandHandle2, Stderr, Stdout
from agentbox.sandbox_async.utils import OutputHandler


class SSHCommands2:
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
            await self.run(f"kill -9 {pid}")
            await handle.close()
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
        proc = await self._start(cmd, envs, user, cwd, timeout, request_timeout, on_stdout, on_stderr, background=background)
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
        background: Union[bool, None] = None,
    ) -> SSHAsyncCommandHandle2:
        client = await self._get_ssh_client()
        env_str = " ".join([f"{k}='{v}'" for k, v in envs.items()]) + " " if envs else ""
        full_cmd = f"cd {cwd} && {env_str}{cmd}" if cwd else f"{env_str}{cmd}"

        if background:
            full_cmd = f"echo $$; {full_cmd}" 

        loop = asyncio.get_event_loop()
        stdin, stdout, stderr = await loop.run_in_executor(
            None,
            lambda: client.exec_command(command=full_cmd, timeout=timeout)
        )

        pid = len(self._processes) + 1000
        first_line = ""
        if background:
            while True:
                # 按照字节一个一个读取直到换行符
                stdout_data = stdout.channel.recv(1)
                if stdout_data:
                    # 解码并拼接
                    first_line += stdout_data.decode('utf-8')
                    # 判断是否读取完第一行（找到换行符）
                    if '\n' in first_line and first_line != "":
                        # 截取第一行，防止读取到第二行
                        first_line = first_line.split('\n')[0]
                        pid = int(first_line)
                        break  # 第一行读取完后退出

        handle = SSHAsyncCommandHandle2(
            pid=pid,
            handle_kill=lambda: self.kill(pid),
            stdout_stream=stdout,
            stderr_stream=stderr,
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
    ) -> SSHAsyncCommandHandle2:
        if pid in self._processes:
            return self._processes[pid]
        raise Exception(f"Process {pid} not found")


Commands2 = SSHCommands2
