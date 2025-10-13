import threading
import socket
import select
import traceback
import paramiko
import re
from typing import Optional, List, Any
import adbutils
import os
import platform
import subprocess
import shlex
import time
from importlib.resources import files


def _retry(func, max_retries=3, delay=1, name=""):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            err_line = ''.join(traceback.format_exception_only(type(e), e)).strip().replace('\n', ' ')
            print(f"[error] <{name}> failed on attempt {attempt + 1}: {err_line}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise
    return None


class ADBShell:
    def __init__(
            self,
            forwarder_command: Optional[str] = None,
            connect_command: Optional[str] = None,
            adb_auth_command: Optional[str] = None,
            adb_auth_password: Optional[str] = None,
            adb_path: Optional[str] = None,
    ):
        match_connect = re.search(r"adb connect ([\d.]+:\d+)", connect_command)
        if match_connect:
            self.remote_addr = match_connect.group(1)
            self.serial = match_connect.group(1)
        else:
            raise ValueError("Invalid adb connect command")

        self._device = None
        self._active = None
        self._adb_path = adb_path
        self._forwarder_command = forwarder_command
        self._connect_command = connect_command
        self._adb_auth_command = adb_auth_command
        self._adb_auth_password = adb_auth_password
        self._ssh_proc = None
        self._set_adb_path()

    def _set_adb_path(self):
        if self._adb_path:
            print(f"Using custom system adb ({self._adb_path})")
            abs_path = os.path.abspath(self._adb_path)
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"ADB binary not found at {abs_path}")
            os.environ["ADBUTILS_ADB_PATH"] = abs_path
        else:
            system = platform.system().lower()
            if system == "darwin":
                abs_path = str(files("agentbox.bin.darwin").joinpath("adb"))
                os.environ["ADBUTILS_ADB_PATH"] = abs_path
                self._adb_path = abs_path
            elif system == "windows":
                abs_path = str(files("agentbox.bin.windows").joinpath("adb"))
                os.environ["ADBUTILS_ADB_PATH"] = abs_path
                self._adb_path = abs_path
            elif system == "linux":
                abs_path = str(files("agentbox.bin.linux").joinpath("adb"))
                os.environ["ADBUTILS_ADB_PATH"] = abs_path
                self._adb_path = abs_path
            else:
                print("Unknown platform; defaulting to system adb")
                self._adb_path = 'adb'

        if self._adb_path:
            con_cmd = self._connect_command
            self._connect_command = con_cmd.replace("adb", shlex.quote(os.path.abspath(self._adb_path)), 1)
            auth_cmd = self._adb_auth_command
            self._adb_auth_command = auth_cmd.replace("adb", shlex.quote(os.path.abspath(self._adb_path)), 1)
        else:
            raise ValueError("Invalid adb path")

    def connect(self):
        if self._active == True:
            return
        # 替换空闲端口(初始化时不抢占端口，连接时进行空闲端口查找和占用)
        free_port, sock = self._get_free_port_above()
        self._forwarder_command = self._forwarder_command.replace("11000:", f"{free_port}:")
        self._connect_command = self._connect_command.replace(":11000", f":{free_port}")
        self._adb_auth_command = self._adb_auth_command.replace(":11000", f":{free_port}")
        match_connect = re.search(r"adb connect ([\d.]+:\d+)", self._connect_command)
        # 替换remote_addr serial
        if match_connect:
            self.remote_addr = match_connect.group(1)
            self.serial = match_connect.group(1)
        else:
            raise ValueError("Invalid adb connect command")
        self._sock = sock
        
        """完成：SSH 转发 -> ADB connect -> adb_auth -> 获取 device"""
        _retry(self._start_ssh_forward, max_retries=3, delay=1, name="SSH forward")
        _retry(self._adb_connect, max_retries=5, delay=1, name="adb connect")
        _retry(self._adb_auth, max_retries=5, delay=1, name="adb auth")

        def _init_device():
            if self.remote_addr:
                adbutils.adb.connect(self.remote_addr)
            if self.serial:
                self._device = adbutils.adb.device(serial=self.serial)
            else:
                self._device = adbutils.adb.device()

        _init_device()
        self._active = True

    def _start_ssh_forward(self):
        m_local_port = re.search(r"-L\s*(\d+):([\d.]+):(\d+)", self._forwarder_command)
        if not m_local_port:
            raise ValueError("forwarder_command does not contain valid -L port forwarding")

        local_port = int(m_local_port.group(1))
        remote_host = m_local_port.group(2)
        remote_port = int(m_local_port.group(3))

        m_ssh_port = re.search(r"-p\s*(\d+)", self._forwarder_command)
        ssh_port = int(m_ssh_port.group(1)) if m_ssh_port else 22

        m_user_host = re.search(r"([^\s@]+)@([^\s ]+)", self._forwarder_command)
        if not m_user_host:
            raise ValueError("forwarder_command does not contain valid user@host")

        ssh_user = m_user_host.group(1)
        ssh_host = m_user_host.group(2)

        if not hasattr(self, '_adb_auth_password') or not self._adb_auth_password:
            raise ValueError("_adb_auth_password is required for SSH password authentication")

        print(f"[*] Starting SSH tunnel to {ssh_user}@{ssh_host}:{ssh_port} forwarding local {local_port} to {remote_host}:{remote_port}")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ssh_host, port=ssh_port, username=ssh_user, password=self._adb_auth_password)
        transport = client.get_transport()

        class ForwardServer(threading.Thread):
            def __init__(self, f_local_port, f_remote_host, f_remote_port, f_transport, sock: socket):
                super().__init__()
                self.local_port = f_local_port
                self.remote_host = f_remote_host
                self.remote_port = f_remote_port
                self.transport = f_transport
                self._stopped = threading.Event()
                self._sock = sock

            def stop(self):
                self._stopped.set()

            def run(self):
                # try:
                    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    # sock.bind(('localhost', self.local_port))
                    # sock.listen(100)
                #     local_port, sock = self._get_sorted_free_port_above()
                #     self.local_port = local_port
                # except Exception as e:
                #     print(f"Failed to bind local port {self.local_port}: {e}")
                #     return

                print(f"Forwarding local port {self.local_port} to {self.remote_host}:{self.remote_port}")

                while not self._stopped.is_set():
                    r, w, x = select.select([self._sock], [], [], 1)
                    if self._sock in r:
                        client_sock, addr = self._sock.accept()
                        try:
                            chan = self.transport.open_channel('direct-tcpip',
                                                               (self.remote_host, self.remote_port),
                                                               client_sock.getpeername())
                        except Exception as e:
                            # 判断是否是 SSH session not active 错误
                            if "SSH session not active" not in str(e):
                                print(f"Failed to open channel: {e}")
                            client_sock.close()
                            continue

                        def handler(chan, client_sock):
                            while True:
                                r, w, x = select.select([chan, client_sock], [], [])
                                if chan in r:
                                    data = chan.recv(1024)
                                    if len(data) == 0:
                                        break
                                    client_sock.send(data)
                                if client_sock in r:
                                    data = client_sock.recv(1024)
                                    if len(data) == 0:
                                        break
                                    chan.send(data)
                            chan.close()
                            client_sock.close()

                        threading.Thread(target=handler, args=(chan, client_sock), daemon=True).start()

                self._sock.close()

        self._forward_server = ForwardServer(local_port, remote_host, remote_port, transport, self._sock)
        self._forward_server.start()
        self._ssh_client = client

    def _get_free_port_above(self, start_port=11000, host=''):
        """从 start_port 往上找第一个可用端口并立即占用"""
        offlinePortList = []
        adb = adbutils.adb
        for d in adb.list():
            if d.state == "offline":
                match = re.match(r".+:(\d+)$", d.serial)
                if match:
                    port = int(match.group(1))
                    offlinePortList.append(port)
        for port in range(start_port, 65535):
            try:
                if port in offlinePortList:
                    continue
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host, port))
                s.listen(100)
                return port, s  # 返回端口号和 socket 对象

            except OSError:
                continue
        raise RuntimeError(f"Failed to find free port above: {start_port}")

    def _adb_connect(self):
        if self._connect_command:
            subprocess.run(shlex.split(self._connect_command), check=True)
        else:
            print("[*] No connect_command provided.")

    def _adb_auth(self):
        if self._adb_auth_command:
            proc = subprocess.Popen(
                shlex.split(self._adb_auth_command),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate(input=self._adb_auth_password + "\n")
            if proc.returncode != 0:
                raise RuntimeError(f"adb_auth failed: {stderr.strip()}")
            print("[*] Auth success.")
        else:
            print("[*] Skipping adb_auth.")

    def shell(self, command: str, timeout: Optional[float] = None) -> str:
        return self._device.shell(command, timeout=timeout)

    def push(self, local: str, remote: str):
        self._device.sync.push(local, remote)

    def pull(self, remote: str, local: str):
        self._device.sync.pull(remote, local)

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

    def remove(self, path: str):
        self._device.shell(f"rm -rf {path}")

    def rename(self, src: str, dst: str):
        self._device.shell(f"mv {src} {dst}")

    def make_dir(self, path: str):
        self._device.shell(f"mkdir -p {path}")

    def watch_dir(self, path: str):
        raise NotImplementedError("watch_dir is not implemented for adbutils.")

    def install(self, apk_path: str, reinstall: bool = False):
        args = [self._adb_path or "adb", "-s", self.serial, "install"]
        if reinstall:
            args.append("-r")
        args.append(apk_path)
        subprocess.run(args, check=True)

    def uninstall(self, package_name: str):
        args = [self._adb_path or "adb", "-s", self.serial, "uninstall", package_name]
        subprocess.run(args, check=True)

    def close(self):
        self._active = False
        if hasattr(self, '_forward_server') and self._forward_server:
            print("[*] Stopping SSH tunnel...")
            self._forward_server.stop()
            self._forward_server.join()
        if hasattr(self, '_ssh_client') and self._ssh_client:
            self._ssh_client.close()
        if hasattr(self, '_ssh_proc') and self._ssh_proc:
            self._ssh_proc.terminate()
            self._ssh_proc.wait()
        # 清除offline状态
        self._disconnect_offline_devices()

    def _disconnect_offline_devices(self):
        adb = adbutils.adb
        for d in adb.list():
            if d.serial == self.serial and d.state == "offline":
                adb.disconnect(d.serial)