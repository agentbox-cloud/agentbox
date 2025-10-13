from typing import Callable, Dict, List, Literal, Optional, Union, overload

import shlex
import paramiko
import time
from agentbox.connection_config import ConnectionConfig, Username
from agentbox.sandbox.commands.main import ProcessInfo
from agentbox.sandbox.commands.command_handle import CommandResult
from agentbox.sandbox_sync.commands_ssh2.command_handle_ssh2 import SSHSyncCommandHandle2, Stderr, Stdout


class SSHCommands2:
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
        self._processes: Dict[int, SSHSyncCommandHandle2] = {}

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
            handle._stdout_stream.close()
            handle._stderr_stream.close()
            self.run(f"kill -9 {pid}")
            handle.close()
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
    ) -> SSHSyncCommandHandle2: ...

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
        handle = self._start(cmd, envs, user, cwd, timeout, background=background)
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
            background: Union[bool, None] = None
    ) -> SSHSyncCommandHandle2:
        """
        Start command using non-interactive shell, return handle.
        """
        client = self._get_ssh_client()

        # 构建完整命令
        full_cmd = "" if not background else "echo $$; "
        if cwd:
            full_cmd += f"cd {cwd} && "
        if envs:
            env_str = " ".join([f"{k}='{v}'" for k, v in envs.items()])
            full_cmd += env_str + " "
        full_cmd += f"{cmd}"
        stdin, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)

        # exit_code = stdout.channel.recv_exit_status()
        # print('exit_code:', exit_code)
        # stderr_lines = stderr.read().decode('utf-8', errors='ignore')
        # stdout_lines = stdout.read().decode('utf-8', errors='ignore')
        # print("STDOUT:\n", "".join(stdout_lines))
        # print("STDERR:\n", stderr_lines)
        # print("Exit code:", exit_code)

        pid = len(self._processes) + 1000
        # 逐行读取 stdout 输出
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
            
        handle = SSHSyncCommandHandle2(
            pid=pid,
            handle_kill=lambda: self.kill(pid),
            stdout_stream=stdout,
            stderr_stream=stderr,
        )
        self._processes[pid] = handle
        return handle

    def connect(
        self,
        pid: int,
        timeout: Optional[float] = 60,
        request_timeout: Optional[float] = None,
    ) -> SSHSyncCommandHandle2:
        """
        Connects to a running command.
        """
        if pid in self._processes:
            return self._processes[pid]
        else:
            raise Exception(f"Process {pid} not found")

# Alias
Commands2 = SSHCommands2
