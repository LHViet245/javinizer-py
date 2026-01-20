import asyncio
import logging
from typing import AsyncGenerator, Set

class LogBroadcaster:
    """
    Singleton service to manage SSE (Server-Sent Events) clients 
    and broadcast log messages to them.
    """
    def __init__(self):
        self.clients: Set[asyncio.Queue] = set()

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Subscribe a new client to the log stream"""
        queue = asyncio.Queue()
        self.clients.add(queue)
        try:
            while True:
                message = await queue.get()
                yield f"data: {message}\n\n"
        finally:
            self.clients.remove(queue)

    def broadcast(self, message: str):
        """Send a message to all connected clients"""
        for queue in self.clients:
            queue.put_nowait(message)

class SSEHandler(logging.Handler):
    """
    Custom logging handler that forwards records to the LogBroadcaster.
    """
    def __init__(self, broadcaster: LogBroadcaster):
        super().__init__()
        self.broadcaster = broadcaster
        # Optional: Set a formatter if needed, otherwise use the message directly
        self.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.broadcaster.broadcast(msg)
        except Exception:
            self.handleError(record)

# Singleton instance
broadcaster = LogBroadcaster()
sse_handler = SSEHandler(broadcaster)
