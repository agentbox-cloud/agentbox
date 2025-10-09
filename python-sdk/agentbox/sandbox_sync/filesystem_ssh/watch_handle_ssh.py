from typing import Optional, Callable, List, Dict
from agentbox.sandbox.filesystem.watch_handle import FilesystemEvent, FilesystemEventType
from agentbox.sandbox_sync.commands_ssh.command_ssh import SSHCommands
from agentbox import SandboxException


class SSHSyncWatchHandle:
    """
    Watch filesystem events by polling over SSH.
    """

    def __init__(
        self,
        commands: SSHCommands,
        path: str,
        recursive: bool = False,
    ):
        self._commands = commands
        self._path = path
        self._recursive = recursive
        self._running = True
        self._last_state = self._get_file_state()

    def stop(self):
        """
        Stop watching the directory.
        """
        self._running = False

    def _get_file_state(self) -> Dict[str, dict]:
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

            result = self._commands.run(cmd)

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

    def _detect_changes(self, old_state, new_state):
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


    def get_new_events(self) -> List[FilesystemEvent]:
        """
        Get the latest events that have occurred in the watched directory
        since the last call, by comparing current state to the last state.
        """
        if not self._running:
            raise SandboxException("The watcher is already stopped")

        current_state = self._get_file_state()
        changes = self._detect_changes(self._last_state, current_state)

        # 更新 last_state
        self._last_state = current_state

        return changes

# Alias for backward compatibility
WatchHandle = SSHSyncWatchHandle