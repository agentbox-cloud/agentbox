import paramiko
import threading
from typing import Dict, Optional, Generator

from agentbox.connection_config import Username, ConnectionConfig
from agentbox.sandbox_sync.commands.command_handle import CommandHandle, PtySize


class Pty:
    def __init__(
        self,
        envd_api_url: str,  # 保留参数但不用
        connection_config: ConnectionConfig,
        pool: Optional[object] = None,  # 保留参数但不用
    ) -> None:
        self._connection_config = connection_config

        self._ssh_client = paramiko.SSHClient()
        self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 简单从 connection_config 拿 host/user/password 模拟
        self._ssh_client.connect(
            hostname=connection_config.domain or 'localhost',
            username='user',
            password='password',  # 或 key
            timeout=connection_config.request_timeout,
        )

    def create(
        self,
        size: PtySize,
        user: Username = "user",
        cwd: Optional[str] = None,
        envs: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = 60,
        request_timeout: Optional[float] = None,
    ) -> CommandHandle:
        """
        创建一个新的伪终端，返回 CommandHandle
        """
        envs = envs or {}

        channel = self._ssh_client.invoke_shell(
            term='xterm-256color',
            width=size.cols,
            height=size.rows
        )

        # 切目录
        if cwd:
            channel.send(f'cd {cwd}\n')

        # 设置环境变量
        for k, v in envs.items():
            channel.send(f'export {k}="{v}"\n')

        # 返回一个 CommandHandle（需要同步实现 CommandHandle）
        handle = CommandHandle(
            pid=id(channel),  # 用对象id模拟 pid
            handle_kill=lambda: self.kill(id(channel)),
            events=self._make_events(channel)
        )
        return handle

    def _make_events(self, channel) -> Generator:
        """
        模拟原有的 events generator：不停从 channel 读取数据
        """
        while True:
            if channel.exit_status_ready():
                break
            if channel.recv_ready():
                data = channel.recv(1024)
                yield data.decode()
        yield "__END__"

    def kill(
        self,
        pid: int,
        request_timeout: Optional[float] = None,
    ) -> bool:
        """
        kill：关闭 ssh channel（这里 pid 是伪造的）
        """
        try:
            # 简单处理：直接关闭 transport
            self._ssh_client.close()
            return True
        except Exception:
            return False

    def send_stdin(
        self,
        pid: int,
        data: bytes,
        request_timeout: Optional[float] = None,
    ) -> None:
        """
        向 shell 发送输入
        """
        # 简单找到 channel（真实场景要记录 pid->channel 对应关系）
        # 假设 self._channel 就是当前 channel
        self._channel.send(data.decode())

    def resize(
        self,
        pid: int,
        size: PtySize,
        request_timeout: Optional[float] = None,
    ) -> None:
        """
        调整终端大小
        """
        self._channel.resize_pty(width=size.cols, height=size.rows)
