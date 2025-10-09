import threading
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from agentbox.api.client.models import SandboxADBPublicInfo
from agentbox.sandbox_sync.sandbox_api import SandboxApi, SandboxInfo

class AdbConnectionPool:
    def __init__(self, host, port, rsa_key_path=None, max_conn=1, auth_timeout_s=1.0):
        self.host = host
        self.port = port
        self.rsa_key_path = rsa_key_path
        self.max_conn = max_conn
        self.auth_timeout_s = auth_timeout_s
        self.signer = None
        self._device = None

        self.pool = []
        self.lock = threading.Lock()

        self.instance_no = None

    def _create_connection(self):
        """创建一个新的连接"""
        self.get_adb_public_info()
        device = AdbDeviceTcp(self.host, self.port)
        device.connect(rsa_keys=[self.signer], auth_timeout_s=self.auth_timeout_s)
        return device

    def get_connection(self):
        """获取一个可用连接，如果没有就新建"""
        with self.lock:
            if self.pool:
                return self.pool.pop()
            elif len(self.pool) < self.max_conn:
                return self._create_connection()
            else:
                raise RuntimeError("No available ADB connections")

    def release_connection(self, conn):
        """释放连接回池中"""
        with self.lock:
            if len(self.pool) < self.max_conn:
                self.pool.append(conn)
            else:
                conn.close()

    def shell(self, cmd):
        """执行命令并自动管理连接"""
        conn = self.get_connection()
        try:
            return conn.shell(cmd)
        except Exception:
            # 可能是连接断开，尝试重连一次
            conn.close()
            conn = self._create_connection()
            return conn.shell(cmd)
        finally:
            self.release_connection(conn)

    def close_all(self):
        """关闭所有连接"""
        with self.lock:
            for conn in self.pool:
                conn.close()
            self.pool.clear()

    def _get_adb_public_info(self):
        """获取adb连接信息"""
        info = SandboxApi._get_adb_public_info()
        self.host = info.host
        self.port = info.port
        self.signer = PythonRSASigner(pub=info.publicKey, priv=info.privateKey)
