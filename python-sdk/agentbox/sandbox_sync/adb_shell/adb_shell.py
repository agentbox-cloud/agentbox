import traceback
from typing import Optional
import time
from agentbox.sandbox_sync.sandbox_api import SandboxApi
from adb_shell.adb_device_async import AdbDeviceTcpAsync
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from agentbox.connection_config import ConnectionConfig
from agentbox.async_runner import async_runner

def _retry(func, max_retries=1, delay=1, name=""):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            err_line = ''.join(traceback.format_exception_only(type(e), e)).strip().replace('\n', ' ')
            print(f"[error] <{name}> failed on attempt {attempt + 1}: {err_line}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise Exception(f"Function {name} failed after {max_retries} attempts") from e
    return None


class ADBShell:
    def __init__(self, connection_config:ConnectionConfig, sandbox_id:str, host=None, port=None, rsa_key_path=None, auth_timeout_s=3.0):
        self.connection_config = connection_config
        self.sandbox_id = sandbox_id
        self.host = host
        self.port = port
        self.rsa_key_path = rsa_key_path
        self.auth_timeout_s = auth_timeout_s
        self.signer = None
        self._device = None
        self.instance_no = None
        self._active = False

    def _adb_connect(self):
        """创建一个新的连接"""
        self._get_adb_public_info()
        time.sleep(1)
        device = AdbDeviceTcpAsync(self.host, self.port)
        # 调用异步 connect()
        async def do_connect():
            await device.connect(rsa_keys=[self.signer],
                                 auth_timeout_s=self.auth_timeout_s)
            return device

        device = async_runner.run(do_connect())

        if device.available:
            self._device = device
        else:
            raise Exception("ADB device not available")


    def connect(self):
        if self._active:
            return
        """adb_shell直连"""
        _retry(self._adb_connect, max_retries=3, delay=1, name="adb_shell connect")
        if self._device and self._device.available:
            # print("ADB 首次连接成功")
            self._active = True
        else:
            raise Exception("Failed to connect to ADB shell: device not available")

    def shell(self, command: str, timeout: Optional[float] = None) -> str:
        """执行命令并自动管理连接"""
        async def do_shell():
            return await self._device.shell(command, timeout_s=timeout)

        try:
            return async_runner.run(do_shell())
        except Exception:
            # 尝试重连
            if not self._device or not self._device.available:
                _retry(self._adb_connect, max_retries=1, delay=1, name="adb_shell reconnect")

            return async_runner.run(do_shell())

    # 同步 push()
    def push(self, local: str, remote: str):
        async def do_push():
            await self._device.push(local, remote)
        return async_runner.run(do_push())

    # 同步 pull()
    def pull(self, remote: str, local: str):
        async def do_pull():
            await self._device.pull(remote, local)
        return async_runner.run(do_pull())

    # def list(self, path: str = ".") -> List[Any]:
    #     return self._device.listdir(path)

    def exists(self, path: str) -> bool:
        cmd = f"ls {path}"
        try:
            output = self.shell(cmd)
            if "No such file" in output or output.strip() == "":
                return False
            return True
        except Exception:
            return False

    # 其他方法保持同步封装（删掉 await）
    def remove(self, path: str):
        self.shell(f"rm -rf {path}")

    def rename(self, src: str, dst: str):
        self.shell(f"mv {src} {dst}")

    def make_dir(self, path: str):
        self.shell(f"mkdir -p {path}")

    def install(self, apk_path: str, reinstall: bool = False):
        cmd = f"pm install {'-r ' if reinstall else ''}{apk_path}"
        self.shell(cmd)

    def uninstall(self, package_name: str):
        self.shell(f"pm uninstall {package_name}")

    def close(self):
        self._active = False
        if self._device:
            async_runner.run(self._device.close())

    def _get_adb_public_info(self):
        config_dict = self.connection_config.__dict__
        config_dict.pop("access_token", None)
        config_dict.pop("api_url", None)

        info = SandboxApi._get_adb_public_info(
            sandbox_id=self.sandbox_id,
            **config_dict,
        )
        self.host = info.adb_ip
        self.port = info.adb_port
        self.signer = PythonRSASigner(pub=info.public_key, priv=info.private_key)
        

