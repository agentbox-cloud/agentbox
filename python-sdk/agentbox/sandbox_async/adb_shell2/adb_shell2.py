import traceback,asyncio
from typing import Optional
from adb_shell.adb_device import AdbDeviceTcp
from agentbox.sandbox_async.sandbox_api import SandboxApi
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from agentbox.connection_config import ConnectionConfig
import inspect

async def _retry_async(func, max_retries=3, delay=1, name=""):
    for attempt in range(max_retries):
        try:
            if inspect.iscoroutinefunction(func):
                # 如果 func 是 async 函数
                return await func()
            else:
                # 如果 func 是普通函数
                return await asyncio.to_thread(func)
        except Exception as e:
            err_line = ''.join(traceback.format_exception_only(type(e), e)).strip().replace('\n', ' ')
            print(f"[error] <{name}> failed on attempt {attempt + 1}: {err_line}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                raise
    return None


class ADBShell2:
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

    async def _adb_connect(self):
        """创建一个新的连接"""
        await self._get_adb_public_info()
        await asyncio.sleep(1)
        device = AdbDeviceTcp(self.host, self.port)
        # 判断connect是否成功
        device.connect(rsa_keys=[self.signer], auth_timeout_s=self.auth_timeout_s)
        if device.available:
            # print("ADB 连接成功")
            self._device = device
        else:
            print("Failed to connect to ADB shell: device not available")


    async def connect(self):
        if self._active:
            return
        """adb_shell直连"""
        await _retry_async(self._adb_connect, max_retries=3, delay=1, name="adb_shell connect")
        if self._device and self._device.available:
            self._active = True
        else:
            raise Exception("Failed to connect to ADB shell: device not available")

    async def shell(self, command: str, timeout: Optional[float] = None) -> str:
        """执行命令并自动管理连接"""
        try:
            return self._device.shell(command, timeout_s=timeout)
        except Exception as e:
            # 可能是连接断开，尝试重连一次
            if not self._device or not self._device.available:
                await _retry_async(self._adb_connect, max_retries=1, delay=1, name="adb_shell reconnect")
            if self._device and self._device.available:
                self._active = True
                return self._device.shell(command, timeout_s=timeout)
            raise Exception("Failed to connect to ADB shell: device not available: {}".format(e))

    async def push(self, local: str, remote: str):
        self._device.push(local, remote)

    async def pull(self, remote: str, local: str):
        self._device.pull(remote, local)

    # def list(self, path: str = ".") -> List[Any]:
    #     return self._device.listdir(path)

    async def exists(self, path: str) -> bool:
        cmd = f"ls {path}"
        try:
            output = await self.shell(cmd)
            if "No such file" in output or output.strip() == "":
                return False
            return True
        except Exception:
            return False

    async def remove(self, path: str):
        self._device.shell(f"rm -rf {path}")

    async def rename(self, src: str, dst: str):
        self._device.shell(f"mv {src} {dst}")

    async def make_dir(self, path: str):
        self._device.shell(f"mkdir -p {path}")

    async def watch_dir(self, path: str):
        raise NotImplementedError("watch_dir is not implemented for adb_shell.")

    async def install(self, apk_path: str, reinstall: bool = False):
        """安装应用"""
        if reinstall:
            self._device.shell(f"pm install -r {apk_path}")
        else:
            self._device.shell(f"pm install {apk_path}")

    async def uninstall(self, package_name: str):
        """卸载应用"""
        self._device.shell(f"pm uninstall {package_name}")

    async def close(self):
        self._active = False
        self._device.close()


    async def _get_adb_public_info(self):
        """获取adb连接信息"""
        config_dict = self.connection_config.__dict__
        config_dict.pop("access_token", None)
        config_dict.pop("api_url", None)

        info = await SandboxApi._get_adb_public_info(
            sandbox_id = self.sandbox_id,
            **config_dict,
            )
        self.host = info.adb_ip
        self.port = info.adb_port
        self.signer = PythonRSASigner(pub=info.public_key, priv=info.private_key)
        

