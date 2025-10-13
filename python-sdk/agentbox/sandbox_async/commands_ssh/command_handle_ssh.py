import asyncio
import inspect
import re
from typing import Optional, Callable, Any, AsyncGenerator, Union, Tuple, Coroutine
from agentbox.sandbox.output_utils import OutputUtils

from agentbox.sandbox.commands.command_handle import (
    CommandExitException,
    CommandResult,
    Stderr,
    Stdout,
    PtyOutput,
)
from agentbox.sandbox_async.utils import OutputHandler


class SSHAsyncCommandHandle:
    """
    SSH-based command execution handle (for invoke_shell).
    """

    def __init__(
        self,
        pid: int,
        handle_kill: Callable[[], Coroutine[Any, Any, bool]],
        channel,
        on_stdout: Optional[OutputHandler[Stdout]] = None,
        on_stderr: Optional[OutputHandler[Stderr]] = None,
        on_pty: Optional[OutputHandler[PtyOutput]] = None,
    ):
        self._pid = pid
        self._handle_kill = handle_kill
        self._channel = channel

        self._stdout: str = ""
        self._stderr: str = ""
        self._result: Optional[CommandResult] = None
        self._iteration_exception: Optional[Exception] = None

        self._on_stdout = on_stdout
        self._on_stderr = on_stderr
        self._on_pty = on_pty

        self._wait = asyncio.create_task(self._handle_channel())

    @property
    def pid(self):
        return self._pid

    @property
    def stdout(self):
        return self._stdout

    @property
    def stderr(self):
        return self._stderr

    @property
    def error(self):
        return self._result.error if self._result else None

    @property
    def exit_code(self):
        return self._result.exit_code if self._result else None

    async def _iterate_channel(self) -> AsyncGenerator[
        Union[
            Tuple[Stdout, None, None],
            Tuple[None, Stderr, None],
            Tuple[None, None, PtyOutput],
        ],
        None,
    ]:
        done_marker = "__CMD_DONE__"
        exit_code: Optional[int] = None

        while not self._channel.closed:
            await asyncio.sleep(0.1)

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

    async def _handle_channel(self):
        try:
            async for stdout, stderr, pty in self._iterate_channel():
                if stdout and self._on_stdout:
                    cb = self._on_stdout(stdout)
                    if inspect.isawaitable(cb):
                        await cb
                if stderr and self._on_stderr:
                    cb = self._on_stderr(stderr)
                    if inspect.isawaitable(cb):
                        await cb
                if pty and self._on_pty:
                    cb = self._on_pty(pty)
                    if inspect.isawaitable(cb):
                        await cb
        except Exception as e:
            self._iteration_exception = e

    async def wait(self, timeout: Optional[float] = 10) -> CommandResult:
        try:
            await asyncio.wait_for(self._wait, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError("Command did not finish within timeout.")
        if self._iteration_exception:
            raise self._iteration_exception
        if self._result.exit_code != 0:
            raise CommandExitException(
                stdout=self._stdout,
                stderr=self._stderr,
                exit_code=self._result.exit_code,
                error=self._result.error,
            )
        return self._result

    async def kill(self) -> bool:
        return await self._handle_kill()

    async def disconnect(self) -> None:
        self._wait.cancel()
        if self._channel:
            self._channel.close()

    async def send_stdin(self, data: str) -> None:
        if self._channel and not self._channel.closed:
            self._channel.send(data)

# Alias
AsyncCommandHandle = SSHAsyncCommandHandle
