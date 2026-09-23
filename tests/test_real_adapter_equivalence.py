"""Integration-only proof across actual, separately launched MCP adapters.

Run in the build integration environment with both public distributions installed.
The minimal seedPEA distribution itself does not depend on Hearthline.
"""
import asyncio
from contextlib import AsyncExitStack
import importlib.util
import json
import os
import sys
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from tests.test_operational_contracts import crossing, charter, pea, seed

pytestmark = pytest.mark.skipif(importlib.util.find_spec("hearthline_mcp") is None, reason="cross-adapter integration requires separately installed toolkit")

def decoded(result):
    assert not result.isError
    return json.loads(next(item.text for item in result.content if item.type == "text"))

def test_real_foundation_equivalence(tmp_path):
    async def run():
        async with AsyncExitStack() as stack:
            sessions = []
            for module in ("seedpea_adapter.server", "hearthline_mcp.server"):
                env = {**os.environ, "HEARTHLINE_STORE_ROOT": str(tmp_path / "store"), "HEARTHLINE_STORE_NAMESPACE":"foundation-equivalence"}
                reader, writer = await stack.enter_async_context(stdio_client(StdioServerParameters(command=sys.executable, args=["-m",module], env=env)))
                session = await stack.enter_async_context(ClientSession(reader, writer))
                await session.initialize()
                sessions.append(session)
            seed_tools = {t.name for t in (await sessions[0].list_tools()).tools}
            public_tools = {t.name for t in (await sessions[1].list_tools()).tools}
            assert seed_tools <= public_tools
            assert "review_institutional_branch_registration_json" not in seed_tools
            cases = [
                ("foundation_status", {}),
                ("pal24_source_profile_resource", {}),
                ("compatibility_profile_resource", {}),
                ("compatibility_profile_resource", {"pal_version":"2.3"}),
                ("pal24_review_resume", {"packet_json":'{}'}),
                ("pal24_review_resources", {"packet_json":'{}'}),
                ("charter_check_contract", {"contract_json":json.dumps(charter())}),
                ("pecan_check_crossing", {"crossing_json":json.dumps(crossing())}),
                ("pea_explain_candidate", {"candidate_json":json.dumps(pea())}),
                ("seed_review_release", {"release_json":json.dumps(seed())}),
                ("source_registry_resource", {"query_json":json.dumps({"operation":"search","term":"CHARTER"})}),
                ("source_registry_resource", {"query_json":json.dumps({"operation":"read","source_id":"PAL","version":"2.2"})}),
                ("pal_review_packet", {"packet_json":'{"operation":[],"account":{}}'}),
                ("pecan_check_crossing", {"crossing_json":'{"grant":1,"grant":2}'}),
            ]
            for tool, arguments in cases:
                results = [decoded(await session.call_tool(tool, arguments)) for session in sessions]
                assert results[0] == results[1], tool
            result = decoded(await sessions[0].call_tool("source_registry_resource", {"query_json":json.dumps({"operation":"search","term":"CHARTER"})}))
            assert len(result["sources"]) == 1 and result["sources"][0]["source_id"] == "CHARTER"
            record = crossing(); record["consent"] = {"status":"MISSING"}
            for session in sessions:
                result = decoded(await session.call_tool("pecan_check_crossing", {"crossing_json":json.dumps(record)}))
                assert result["current_usability"] == "UNRESOLVED_REVIEW_REQUIRED"
                assert result["execution_effect"] == "NONE"
    asyncio.run(run())
