import json
import unittest

from mcp.server.fastmcp import FastMCP
from seedpea_foundation.mcp_tools import register_foundation


class SharedMCPFoundationTests(unittest.TestCase):
    def test_two_adapter_surfaces_return_identical_foundation_results(self):
        first, second = FastMCP("seedpea"), FastMCP("hearthline")
        register_foundation(first)
        register_foundation(second)
        packet = json.dumps({"operation": "snapshot", "account": {}, "receipts": []})
        left = first._tool_manager._tools["pal_review_packet"].fn(packet)
        right = second._tool_manager._tools["pal_review_packet"].fn(packet)
        self.assertEqual(left, right)
        self.assertEqual(left["authority_effect"], "NONE")
        self.assertEqual(left["execution_effect"], "NONE")

    def test_institution_profile_is_opt_in(self):
        minimal = FastMCP("minimal")
        institution = FastMCP("institution")
        register_foundation(minimal)
        register_foundation(institution, include_institution=True)
        self.assertNotIn("review_institutional_branch_registration_json", minimal._tool_manager._tools)
        self.assertIn("review_institutional_branch_registration_json", institution._tool_manager._tools)


if __name__ == "__main__":
    unittest.main()
