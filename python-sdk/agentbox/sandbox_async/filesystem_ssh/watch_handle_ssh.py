import asyncio
import inspect
from typing import Optional, Dict

from agentbox.sandbox.filesystem.watch_handle import FilesystemEvent, FilesystemEventType
from agentbox.sandbox_async.utils import OutputHandler
from agentbox.sandbox_async.commands_ssh.command_ssh import SSHCommands


class SSHAsyncWatchHandle:
    """
    SSH-based handle for watching a directory in the sandbox filesystem.

    Use `.stop()` to stop watching the directory.
    """

    def __init__(
        self,
        commands: SSHCommands,
        path: str,
        on_event: OutputHandler[FilesystemEvent],
        on_exit: Optional[OutputHandler[Exception]] = None,
        recursive: bool = False,
    ):
        self._commands = commands
        self._path = path
        self._on_event = on_event
        self._on_exit = on_exit
        self._recursive = recursive
        self._running = True

        self._last_state: Dict[str, dict] = {}
        self._wait: Optional[asyncio.Task] = None

    @classmethod
    async def create(
        cls,
        commands: SSHCommands,
        path: str,
        on_event: OutputHandler[FilesystemEvent],
        on_exit: Optional[OutputHandler[Exception]] = None,
        recursive: bool = False,
    ) -> "SSHAsyncWatchHandle":
        self = cls(commands, path, on_event, on_exit, recursive)
        self._last_state = await self._get_file_state()
        self._wait = asyncio.create_task(self._handle_events())
        return self

    async def stop(self):
        """
        Stop watching the directory.
        """
        self._running = False
        self._wait.cancel()

    # async def _get_file_state(self):
    #     """Get current state of files in the directory"""
    #     try:
    #         # Use find command to get file list
    #         if self._recursive:
    #             cmd = f"find {self._path} -type f -o -type d 2>/dev/null || true"
    #         else:
    #             cmd = f"ls -la {self._path} 2>/dev/null || true"
            
    #         result = await self._commands.run(cmd)
    #         if result.exit_code != 0:
    #             raise Exception(f"Error getting file state: {result.stderr}")

    #         current_state = {}
    #         for line in result.stdout.strip().split('\n'):
    #             if line.strip():
    #                 if self._recursive:
    #                     # Parse find output
    #                     parts = line.strip().split()
    #                     if len(parts) >= 1:
    #                         file_path = parts[0]
    #                         if os.path.isfile(file_path):
    #                             current_state[file_path] = 'file'
    #                         elif os.path.isdir(file_path):
    #                             current_state[file_path] = 'dir'
    #                 else:
    #                     # Parse ls output
    #                     parts = line.strip().split()
    #                     if len(parts) >= 8:
    #                         file_type = parts[0][0]
    #                         file_name = parts[-1]
    #                         if file_name not in ['.', '..']:
    #                             file_path = os.path.join(self._path, file_name)
    #                             if file_type == 'd':
    #                                 current_state[file_path] = 'dir'
    #                             else:
    #                                 current_state[file_path] = 'file'
            
    #         return current_state
    #     except Exception:
    #         return {}

    async def _get_file_state(self) -> Dict[str, dict]:
        """
        Async: Get detailed file state: path -> {type, size, mtime, mode, inode}
        """
        try:
            if self._recursive:
                cmd = (
                    f"find {self._path} \\( -type f -o -type d \\) 2>/dev/null | "
                    f"while read -r f; do stat -c '%n|%F|%s|%Y|%a|%i' \"$f\"; done 2>/dev/null || true"
                )
            else:
                cmd = f"stat -c '%n|%F|%s|%Y|%a|%i' {self._path}/* 2>/dev/null || true"

            result = await self._commands.run(cmd)

            if result.exit_code != 0:
                raise Exception(f"Error getting file state: {result.stderr}")

            current_state = {}
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    path, ftype, size, mtime, mode, inode = line.strip().split("|")
                    current_state[path] = {
                        "type": "dir" if "directory" in ftype else "file",
                        "size": int(size),
                        "mtime": int(mtime),
                        "mode": mode,
                        "inode": inode,
                        "flag": f"{inode}:{size}:{mtime}:{mode}"
                    }
                except ValueError:
                    continue

            return current_state
        except Exception as e:
            print(f"[get_file_state] Error: {e}")
            return {}

    # async def _detect_changes(self, old_state, new_state):
    #     """Detect changes between old and new file states"""
    #     changes = []
        
    #     # Check for new files
    #     for path, file_type in new_state.items():
    #         if path not in old_state:
    #             changes.append(FilesystemEvent(
    #                 name=os.path.basename(path),
    #                 type=file_type
    #             ))
        
    #     # Check for deleted files
    #     for path, file_type in old_state.items():
    #         if path not in new_state:
    #             changes.append(FilesystemEvent(
    #                 name=os.path.basename(path),
    #                 type=file_type
    #             ))
        
    #     return changes
    
    async def _detect_changes(self, old_state, new_state):
        changes = []

        old_paths = set(old_state.keys())
        new_paths = set(new_state.keys())

        created = new_paths - old_paths
        deleted = old_paths - new_paths

        matched_renames = set()
        matched_old_paths = set()

        # 1. RENAME
        for old_path in deleted:
            old_flag = old_state[old_path]["flag"]
            for new_path in created:
                if new_path in matched_renames:
                    continue
                new_flag = new_state[new_path]["flag"]
                if old_flag == new_flag:
                    changes.append(FilesystemEvent(name=new_path, type=FilesystemEventType.RENAME))
                    matched_renames.add(new_path)
                    matched_old_paths.add(old_path)
                    break

        # 2. CREATE
        for path in created - matched_renames:
            changes.append(FilesystemEvent(name=path, type=FilesystemEventType.CREATE))

        # 3. REMOVE
        for path in deleted - matched_old_paths:
            changes.append(FilesystemEvent(name=path, type=FilesystemEventType.REMOVE))

        # 4. WRITE / CHMOD
        for path in old_paths & new_paths:
            old = old_state[path]
            new = new_state[path]

            if old["mtime"] != new["mtime"] or old["size"] != new["size"]:
                changes.append(FilesystemEvent(name=path, type=FilesystemEventType.WRITE))
            elif old["mode"] != new["mode"]:
                changes.append(FilesystemEvent(name=path, type=FilesystemEventType.CHMOD))

        return changes


    async def _iterate_events(self):
        """Iterate through filesystem events"""
        while self._running:
            try:
                current_state = await self._get_file_state()
                changes = await self._detect_changes(self._last_state, current_state)
                
                for change in changes:
                    yield change
                
                self._last_state = current_state
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                if self._on_exit:
                    cb = self._on_exit(e)
                    if inspect.isawaitable(cb):
                        await cb
                break

    async def _handle_events(self):
        """Handle filesystem events"""
        try:
            async for event in self._iterate_events():
                if not self._running:
                    break
                    
                cb = self._on_event(event)
                if inspect.isawaitable(cb):
                    await cb
        except Exception as e:
            if self._on_exit:
                cb = self._on_exit(e)
                if inspect.isawaitable(cb):
                    await cb


# Alias for backward compatibility
AsyncWatchHandle = SSHAsyncWatchHandle