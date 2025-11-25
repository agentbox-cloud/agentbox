# agentbox/async_runner.py

import asyncio
import threading


class AsyncRunner:
    """Singleton runner that keeps a background event loop for async tasks."""
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro):
        """Run async coroutine synchronously and return its result."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()


# Global singleton, used throughout the SDK
async_runner = AsyncRunner()
