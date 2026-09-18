"""Standalone transport smoke test for the minimal SeedPEA adapter."""

from __future__ import annotations

import asyncio
import os
import sys
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_minimal_adapter_stdio_round_trip() -> None:
    async def run() -> None:
        environment = {**os.environ, "SEEDPEA_PROFILE": "minimal"}
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "seedpea_adapter.server"],
            env=environment,
        )
        async with AsyncExitStack() as stack:
            reader, writer = await stack.enter_async_context(stdio_client(parameters))
            session = await stack.enter_async_context(ClientSession(reader, writer))
            info = await session.initialize()
            assert info.serverInfo.name == "seedpea-mcp-adapter"

            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert {"foundation_status", "pal_review_packet", "pecan_check_crossing"} <= names

            result = await session.call_tool("foundation_status", {})
            assert result.isError is False
            assert result.content

    asyncio.run(run())
