from collections.abc import AsyncGenerator
from typing import Any


async def stream_mock_agent_events(user_input: str) -> AsyncGenerator[dict[str, Any], None]:
    yield {
        "event": "chat_chunk",
        "data": {
            "content": f"Mock Moss response: {user_input}",
            "done": True,
        },
    }
