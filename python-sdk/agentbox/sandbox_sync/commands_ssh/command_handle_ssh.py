from typing import Optional, Callable, Generator, Union, Tuple

from agentbox.sandbox.commands.command_handle import (
    CommandExitException,
    CommandResult,
    Stderr,
    Stdout,
    PtyOutput,
)
from agentbox.sandbox.output_utils import OutputUtils



class SSHSyncCommandHandle:
    """
    Command execution handle.

    It provides methods for waiting for the command to finish, retrieving stdout/stderr, and killing the command.
    """

    def __init__(
        self,
        pid: int,
        handle_kill: Callable[[], bool],
        channel,
    ):
        self._pid = pid
        self._handle_kill = handle_kill
        self._channel = channel

        self._stdout: str = ""
        self._stderr: str = ""

        self._result: Optional[CommandResult] = None

    @property
    def pid(self):
        """
        Command process ID.
        """
        return self._pid

    def __iter__(self):
        """
        Iterate over the command output.

        :return: Generator of command outputs
        """
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
        done_marker = "__CMD_DONE__"
        exit_code: Optional[int] = None

        while not self._channel.closed:
            if self._channel.recv_ready():
                chunk = self._channel.recv(1024).decode("utf-8", "replace")
                self._stdout += chunk
                yield chunk, None, None

                # ✅ 检查是否出现完成标志, 注意交互式shell取后面的字符串
                last_chars = chunk[-(len(done_marker) + 6):]
                if done_marker in last_chars:
                    for line in chunk.strip().splitlines():
                        if line.startswith(done_marker):
                            try:
                                exit_code = int(line[len(done_marker):])
                            except ValueError:
                                exit_code = -1
                            break
                    self._channel.close()
                    break

            if self._channel.recv_stderr_ready():
                chunk = self._channel.recv_stderr(1024).decode("utf-8", "replace")
                self._stderr += chunk
                yield None, chunk, None

        # 最终构造 result & 清理交互式shell无用信息
        self._stdout = OutputUtils.strip_echo_and_prompt(self._stdout)
        self._result = CommandResult(
            stdout=self._stdout,
            stderr=self._stderr,
            exit_code=exit_code if exit_code is not None else -1,
            error=None if exit_code == 0 else f"Command exited with code {exit_code}",
        )

    def disconnect(self) -> None:
        """
        Disconnect from the command.

        The command is not killed, but SDK stops receiving events from the command.
        You can reconnect to the command using `sandbox.commands.connect` method.
        """
        if self._channel:
            self._channel.close()

    def wait(
        self,
        on_pty: Optional[Callable[[PtyOutput], None]] = None,
        on_stdout: Optional[Callable[[str], None]] = None,
        on_stderr: Optional[Callable[[str], None]] = None,
    ) -> CommandResult:
        """
        Wait for the command to finish and returns the result.
        If the command exits with a non-zero exit code, it throws a `CommandExitException`.
        """
        
        try:
            for stdout, stderr, pty in self:
                if stdout is not None and on_stdout:
                    on_stdout(stdout)
                elif stderr is not None and on_stderr:
                    on_stderr(stderr)
                elif pty is not None and on_pty:
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
        return CommandResult(
                stdout=self._stdout,
                stderr=self._stderr,
                exit_code=self._result.exit_code,
                error=self._result.error,
            )

    def kill(self) -> bool:
        """
        Kills the command.

        It uses `SIGKILL` signal to kill the command.

        :return: Whether the command was killed successfully
        """
        return self._handle_kill()

# Alias
CommandHandle = SSHSyncCommandHandle