import os
import shlex

from io import IOBase
from typing import AsyncIterator, IO, List, Literal, Optional, overload, Union

from agentbox.connection_config import (
    ConnectionConfig,
    Username,
)
from agentbox.exceptions import InvalidArgumentException
from agentbox.sandbox.filesystem.filesystem import EntryInfo, WriteEntry, FileType
from agentbox.sandbox.filesystem.watch_handle import FilesystemEvent
from agentbox.sandbox_async.filesystem_ssh.watch_handle_ssh import SSHAsyncWatchHandle
from agentbox.sandbox_async.utils import OutputHandler
from agentbox.sandbox_async.commands_ssh.command_ssh import SSHCommands
from agentbox import CommandExitException


class SSHFilesystem:
    """
    SSH-based module for interacting with the filesystem in the sandbox.
    """

    def __init__(
        self,
        ssh_host: str,
        ssh_port: int,
        ssh_username: str,
        ssh_password: str,
        connection_config: ConnectionConfig,
        commands: SSHCommands,
        watch_commands: SSHCommands,
    ) -> None:
        self._ssh_host = ssh_host
        self._ssh_port = ssh_port
        self._ssh_username = ssh_username
        self._ssh_password = ssh_password
        self._connection_config = connection_config
        self._commands = commands
        self._watch_commands = watch_commands

    @overload
    async def read(
        self,
        path: str,
        format: Literal["text"] = "text",
        user: Username = "user",
        request_timeout: Optional[float] = None,
    ) -> str:
        """
        Read file content as a `str`.

        :param path: Path to the file
        :param user: Run the operation as this user
        :param format: Format of the file content—`text` by default
        :param request_timeout: Timeout for the request in **seconds**

        :return: File content as a `str`
        """
        ...

    @overload
    async def read(
        self,
        path: str,
        format: Literal["bytes"],
        user: Username = "user",
        request_timeout: Optional[float] = None,
    ) -> bytearray:
        """
        Read file content as a `bytearray`.

        :param path: Path to the file
        :param user: Run the operation as this user
        :param format: Format of the file content—`bytes`
        :param request_timeout: Timeout for the request in **seconds**

        :return: File content as a `bytearray`
        """
        ...

    @overload
    async def read(
        self,
        path: str,
        format: Literal["stream"],
        user: Username = "user",
        request_timeout: Optional[float] = None,
    ) -> AsyncIterator[bytes]:
        """
        Read file content as a `AsyncIterator[bytes]`.

        :param path: Path to the file
        :param user: Run the operation as this user
        :param format: Format of the file content—`stream`
        :param request_timeout: Timeout for the request in **seconds**

        :return: File content as an `AsyncIterator[bytes]`
        """
        ...

    async def read(
        self,
        path: str,
        format: Literal["text", "bytes", "stream"] = "text",
        user: Username = "user",
        request_timeout: Optional[float] = None,
    ):
        cmd = f"cat {path}"
        result = await self._commands.run(cmd)
        return result.stdout

    @overload
    async def write(
        self,
        path: str,
        data: Union[str, bytes, IO],
        user: Username = "user",
        request_timeout: Optional[float] = None,
    ) -> EntryInfo:
        """
        Write content to a file on the path.

        Writing to a file that doesn't exist creates the file.

        Writing to a file that already exists overwrites the file.

        Writing to a file at path that doesn't exist creates the necessary directories.

        :param path: Path to the file
        :param data: Data to write to the file, can be a `str`, `bytes`, or `IO`.
        :param user: Run the operation as this user
        :param request_timeout: Timeout for the request in **seconds**

        :return: Information about the written file
        """

    @overload
    async def write(
        self,
        files: List[WriteEntry],
        user: Optional[Username] = "user",
        request_timeout: Optional[float] = None,
    ) -> List[EntryInfo]:
        """
        Writes multiple files.

        :param files: list of files to write
        :param user: Run the operation as this user
        :param request_timeout: Timeout for the request
        :return: Information about the written files
        """

    async def write(
        self,
        path_or_files: Union[str, List[WriteEntry]],
        data_or_user: Union[str, bytes, IO, Username] = "user",
        user_or_request_timeout: Optional[Union[float, Username]] = None,
        request_timeout_or_none: Optional[float] = None,
    ) -> Union[EntryInfo, List[EntryInfo]]:
        """
        Writes content to a file on the path.
        When writing to a file that doesn't exist, the file will get created.
        When writing to a file that already exists, the file will get overwritten.
        When writing to a file that's in a directory that doesn't exist, you'll get an error.
        """
        path, write_files, user, request_timeout = None, [], "user", None
        if isinstance(path_or_files, str):
            if isinstance(data_or_user, list):
                raise Exception(
                    "Cannot specify both path and array of files. You have to specify either path and data for a single file or an array for multiple files."
                )
            path, write_files, user, request_timeout = (
                path_or_files,
                [{"path": path_or_files, "data": data_or_user}],
                user_or_request_timeout or "user",
                request_timeout_or_none,
            )
        else:
            if path_or_files is None:
                raise Exception("Path or files are required")
            path, write_files, user, request_timeout = (
                None,
                path_or_files,
                data_or_user,
                user_or_request_timeout,
            )

        results = []
        for file in write_files:
            file_path, file_data = file["path"], file["data"]
            
            # Ensure directory exists
            dir_path = os.path.dirname(file_path)
            if dir_path:
                await self.make_dir(dir_path, user, request_timeout)

            # Convert data to string or bytes
            if isinstance(file_data, str):
                data_str = file_data
            elif isinstance(file_data, bytes):
                data_str = file_data.decode('utf-8', 'replace')
            elif isinstance(file_data, IOBase):
                data_str = file_data.read()
                if isinstance(data_str, bytes):
                    data_str = data_str.decode('utf-8', 'replace')
            else:
                raise ValueError(f"Unsupported data type for file {file_path}")
            
            # Write file using echo and redirection
            # Escape the data to handle special characters
            escaped_data = data_str.replace("'", "'\"'\"'")
            cmd = f"echo '{escaped_data}' > '{file_path}'"
            runRet = await self._commands.run(cmd)
            if runRet.exit_code != 0:
                raise Exception(f"Failed to write file {file_path}")
            
            # Get file info
            file_info = await self._get_file_info(file_path)
            results.append(file_info)

        if len(results) == 1 and path:
            return results[0]
        else:
            return results

    async def list(
        self,
        path: str,
        depth: Optional[int] = 1,
        user: Username = "user",
        request_timeout: Optional[float] = None,
    ) -> List[EntryInfo]:
        """
        List entries in a directory.

        :param path: Path to the directory
        :param depth: Depth of the directory to list
        :param user: Run the operation as this user
        :param request_timeout: Timeout for the request in **seconds**

        :return: List of entries in the directory
        """
        if depth is not None and depth < 1:
            raise InvalidArgumentException("depth should be at least 1")
        
        # Use ls command to list directory contents
        if depth == 1:
            cmd = f"ls -la '{path}' 2>/dev/null || true"
        else:
            # For deeper listing, use find with maxdepth
            cmd = f"find '{path}' -maxdepth {depth} -type f -o -type d 2>/dev/null || true"

        result = await self._commands.run(cmd)
        if result.exit_code != 0:
            raise Exception(f"Failed to list directory {path}")
        
        entries = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                if depth == 1:
                    # Parse ls output
                    parts = line.strip().split()
                    if len(parts) >= 8:
                        file_type = parts[0][0]
                        file_name = parts[-1]
                        if file_name not in ['.', '..']:
                            file_path = os.path.join(path, file_name)
                            if file_type == 'd':
                                entries.append(EntryInfo(
                                    name=file_name,
                                    type=FileType.DIR,
                                    path=file_path
                                ))
                            else:
                                entries.append(EntryInfo(
                                    name=file_name,
                                    type=FileType.FILE,
                                    path=file_path
                                ))
                else:
                    # Parse find output
                    parts = line.strip().split()
                    if len(parts) >= 1:
                        file_path = parts[0]
                        file_name = os.path.basename(file_path)
                        if os.path.isdir(file_path):
                            entries.append(EntryInfo(
                                name=file_name,
                                type=FileType.DIR,
                                path=file_path
                            ))
                        else:
                            entries.append(EntryInfo(
                                name=file_name,
                                type=FileType.FILE,
                                path=file_path
                            ))
        
        return entries

    async def exists(
        self,
        path: str,
        user: Username = "user",
        request_timeout: Optional[float] = None,
    ) -> bool:
        """
        Check if a file or a directory exists.

        :param path: Path to a file or a directory
        :param user: Run the operation as this user
        :param request_timeout: Timeout for the request in **seconds**

        :return: `True` if the file or directory exists, `False` otherwise
        """
        command = f"test -e {shlex.quote(path)}"

        try:
            result = await self._commands.run(command, user=user, request_timeout=request_timeout)
            if result.exit_code == 0:
                return True
            elif result.exit_code == 1:
                return False  # 文件不存在
            else:
                raise Exception(f"[test -e] Unexpected exit code {result.exit_code} for path '{path}': {result.stderr.strip()}")

        except CommandExitException as e:
            stderr = e.stderr.strip() if e.stderr else ""
            if stderr:
                raise Exception(f"[test -e] CommandExitException while checking path '{path}': {stderr}")
            return False  # 默认为不存在

        except Exception as e:
            raise Exception(f"[test -e] Unexpected error while checking path '{path}': {e}") from e

    async def remove(
        self,
        path: str,
        user: Username = "user",
        request_timeout: Optional[float] = None,
    ) -> None:
        """
        Remove a file or a directory.

        :param path: Path to a file or a directory
        :param user: Run the operation as this user
        :param request_timeout: Timeout for the request in **seconds**
        """
        result = await self._commands.run(f"rm -rf '{path}'")
        if result.exit_code != 0:
            raise Exception(f"Failed to remove {path}")

    async def rename(
        self,
        old_path: str,
        new_path: str,
        user: Username = "user",
        request_timeout: Optional[float] = None,
    ) -> EntryInfo:
        """
        Rename a file or directory.

        :param old_path: Path to the file or directory to rename
        :param new_path: New path to the file or directory
        :param user: Run the operation as this user
        :param request_timeout: Timeout for the request in **seconds**

        :return: Information about the renamed file or directory
        """
        result = await self._commands.run(f"mv '{old_path}' '{new_path}'")
        if result.exit_code != 0:
            raise Exception(f"Failed to rename {old_path} to {new_path}")
        
        return await self._get_file_info(new_path)

    async def make_dir(
        self,
        path: str,
        user: Username = "user",
        request_timeout: Optional[float] = None,
    ) -> bool:
        """
        Create a new directory and all directories along the way if needed on the specified path.

        :param path: Path to a new directory. For example '/dirA/dirB' when creating 'dirB'.
        :param user: Run the operation as this user
        :param request_timeout: Timeout for the request in **seconds**

        :return: `True` if the directory was created, `False` if the directory already exists
        """
        # Check if directory already exists
        if await self.exists(path, user, request_timeout):
            return False

        await self._commands.run(f"mkdir -p '{path}'")
        return True

    async def watch_dir(
        self,
        path: str,
        on_event: OutputHandler[FilesystemEvent],
        on_exit: Optional[OutputHandler[Exception]] = None,
        user: Username = "user",
        request_timeout: Optional[float] = None,
        timeout: Optional[float] = 60,
        recursive: bool = False,
    ) -> SSHAsyncWatchHandle:
        """
        Watch directory for filesystem events.

        :param path: Path to a directory to watch
        :param on_event: Callback to call on each event in the directory
        :param on_exit: Callback to call when the watching ends
        :param user: Run the operation as this user
        :param request_timeout: Timeout for the request in **seconds**
        :param timeout: Timeout for the watch operation in **seconds**. Using `0` will not limit the watch time
        :param recursive: Watch directory recursively

        :return: `SSHWatchHandle` object for stopping watching directory
        """
        return await SSHAsyncWatchHandle.create(
            commands=self._watch_commands,
            path=path,
            on_event=on_event,
            on_exit=on_exit,
            recursive=recursive,
        )

    async def _get_file_info(self, path: str) -> EntryInfo:
        """Get file information"""
        result = await self._commands.run(f"ls -ld '{path}' 2>/dev/null || true")
        if result.exit_code != 0:
            raise Exception(f"File {path} not found")

        parts = result.stdout.strip().split()
        if len(parts) >= 8:
            file_type = parts[0][0]
            file_name = os.path.basename(path)
            
            if file_type == 'd':
                return EntryInfo(
                    name=file_name,
                    type=FileType.DIR,
                    path=path
                )
            else:
                return EntryInfo(
                    name=file_name,
                    type=FileType.FILE,
                    path=path
                )
        else:
            raise Exception(f"Could not parse file info for {path}")


# Alias for backward compatibility
Filesystem = SSHFilesystem 