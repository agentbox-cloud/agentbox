import asyncio
import inspect
from typing import Optional, Callable, Any, Coroutine

from agentbox.sandbox.commands.command_handle import (
    CommandExitException,
    CommandResult,
    Stderr,
    Stdout,
)
from agentbox.sandbox_async.utils import OutputHandler


class SSHAsyncCommandHandle2:
    def __init__(
        self,
        pid: int,
        handle_kill: Callable[[], Coroutine[Any, Any, bool]],
        stdout_stream,
        stderr_stream,
        on_stdout: Optional[OutputHandler[Stdout]] = None,
        on_stderr: Optional[OutputHandler[Stderr]] = None,
    ):
        self._pid = pid
        self._handle_kill = handle_kill
        self._stdout_stream = stdout_stream
        self._stderr_stream = stderr_stream

        self._stdout = ""
        self._stderr = ""
        self._result: Optional[CommandResult] = None
        self._iteration_exception: Optional[Exception] = None

        self._on_stdout = on_stdout
        self._on_stderr = on_stderr

        self._wait = asyncio.create_task(self._read_output())

        self._closed = False
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

    async def _read_output(self):
        try:
            # async def read_stream(stream, attr_name, callback):
            #     while True:
            #         line = await asyncio.get_event_loop().run_in_executor(None, stream.readline)
            #         if not line:
            #             break
            #         setattr(self, attr_name, getattr(self, attr_name) + line)
            #         if callback:
            #             result = callback(line)
            #             if inspect.isawaitable(result):
            #                 await result
            async def read_stream(stream, attr_name, callback):
                loop = asyncio.get_event_loop()

                def read_chunk():
                    try:
                        return stream.read(1024)
                    except Exception:
                        return b""

                while True:
                    chunk = await loop.run_in_executor(None, read_chunk)
                    if not chunk:
                        break

                    text = chunk.decode("utf-8", errors="ignore")
                    setattr(self, attr_name, getattr(self, attr_name) + text)

                    if callback:
                        result = callback(text)
                        if inspect.isawaitable(result):
                            await result

            stdout_task = asyncio.create_task(read_stream(self._stdout_stream, "_stdout", self._on_stdout))
            stderr_task = asyncio.create_task(read_stream(self._stderr_stream, "_stderr", self._on_stderr))

            await asyncio.gather(stdout_task, stderr_task)

            exit_code = self._stdout_stream.channel.recv_exit_status()
            self._result = CommandResult(
                stdout=self._stdout,
                stderr=self._stderr,
                exit_code=exit_code,
                error=None if exit_code == 0 else f"Command exited with code {exit_code}",
            )
        except Exception as e:
            self._iteration_exception = e

    async def wait(self, timeout: Optional[float] = 10) -> CommandResult:
        try:
            if self._closed:
                # 进程已停止，错误提示
                self._stdout = ""
                self._stderr = f"Command(pid:{self._pid}) has been closed\n"
                self._result = CommandResult(
                    stdout=self._stdout,
                    stderr=self._stderr,
                    exit_code=1,
                    error=None,
                )
                # 关闭输出流
                self._stdout_stream.channel.close()
                self._stderr_stream.channel.close()
                return self._result
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

    async def send_stdin(self, data: str) -> None:
        if self._stdout_stream.channel.send_ready():
            self._stdout_stream.channel.send(data)

    async def close(self) -> None:
        self._closed=True

# Alias
AsyncCommandHandle2 = SSHAsyncCommandHandle2