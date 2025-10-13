from typing import Optional, Callable, Generator, Union, Tuple, IO, LiteralString
from paramiko.channel import ChannelFile
from paramiko import SSHClient
import os

from agentbox.sandbox.commands.command_handle import (
    CommandExitException,
    CommandResult,
    Stderr,
    Stdout,
    PtyOutput,
)


class SSHSyncCommandHandle2:
    """
    SSH command execution handle (sync version).

    Supports reading from stdout/stderr streams synchronously,
    capturing outputs, and yielding them progressively.
    """

    def __init__(
        self,
        pid: int,
        handle_kill: Callable[[], bool],
        stdout_stream: ChannelFile,
        stderr_stream: ChannelFile,
    ):
        self._pid = pid
        self._handle_kill = handle_kill
        self._stdout_stream = stdout_stream
        self._stderr_stream = stderr_stream

        self._stdout: str = ""
        self._stderr: str = ""
        self._result: Optional[CommandResult] = None
        self._closed = False

    @property
    def pid(self) -> int:
        return self._pid

    def __iter__(self):
        return self._handle_events()

    def _handle_events(
        self,
    ) -> Generator[
        Union[
            Tuple[Stdout, None, None],
            Tuple[None, Stderr, None],
            Tuple[None, None, PtyOutput],
        ],
        None,
        None,
    ]:
        stdout_chunks = []
        stderr_chunks = []

        def read_stream(stream: IO[bytes], chunks: list, is_stdout: bool):
            while True:
                line = stream.readline()
                if not line:
                    break
                # text = line.decode("utf-8", "replace")
                text = line
                chunks.append(text)
                if is_stdout:
                    yield (text, None, None)
                else:
                    yield (None, text, None)

        # Read stdout then stderr
        if not self._closed:
            yield from read_stream(self._stdout_stream, stdout_chunks, True)
            yield from read_stream(self._stderr_stream, stderr_chunks, False)
            self._stdout = "".join(stdout_chunks)
            self._stderr = "".join(stderr_chunks)
            # Wait for exit code
            exit_code = self._stdout_stream.channel.recv_exit_status()
        else:
            # 模拟流式输出
            self._stdout = ""
            self._stderr = f"Command(pid:{self._pid}) has been closed\n"
            yield (self._stdout, None, None)
            yield (None, self._stderr, None)
            exit_code = 1

        self._result = CommandResult(
            stdout=self._stdout,
            stderr=self._stderr,
            exit_code=exit_code,
            error=None if exit_code == 0 else f"Command exited with code {exit_code}",
        )

    def wait(
        self,
        on_pty: Optional[Callable[[PtyOutput], None]] = None,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
    ) -> CommandResult:
        try:
            if self._closed:
                self._stdout = ""
                self._stderr = f"Command(pid:{self._pid}) has been closed\n"
                self._result = CommandResult(
                    stdout=self._stdout,
                    stderr=self._stderr,
                    exit_code=1,
                    error=None,
                )
                return self._result

            for stdout, stderr, pty in self:
                if stdout and on_stdout:
                    on_stdout(stdout)
                elif stderr and on_stderr:
                    on_stderr(stderr)
                elif pty and on_pty:
                    on_pty(pty)
        except Exception as e:
            raise e

        if self._result is None:
            raise Exception("Command ended without an end event")

        if self._result.exit_code != 0:
            raise CommandExitException(
                stdout=self._stdout,
                stderr=self._stderr,
                exit_code=self._result.exit_code,
                error=self._result.error,
            )
        return self._result

    def kill(self) -> bool:
        return self._handle_kill()

    def disconnect(self) -> None:
        try:
            self._stdout_stream.channel.close()
        except Exception:
            pass

    def close(self) -> None:
        self._closed = True


# Alias
SyncCommandHandle2 = SSHSyncCommandHandle2
