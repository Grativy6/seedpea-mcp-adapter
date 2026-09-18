import json
import unittest

from seedpea_foundation.contracts import (
    CHARTER_FIELDS, PECAN_FIELDS, PEA_FIELDS, SEED_FIELDS,
    check_charter_contract, check_pecan_crossing, explain_pea_candidate,
    review_seed_release, review_pal_packet,
)
from seedpea_foundation.mcp_tools import _peaches_prepare, _review


class FoundationNegativeBoundaryTests(unittest.TestCase):
    def test_non_object_profiles_are_invalid(self):
        for checker in (review_pal_packet, check_charter_contract,
                        check_pecan_crossing, explain_pea_candidate,
                        review_seed_release):
            with self.subTest(checker=checker.__name__):
                result = checker([])
                self.assertEqual(result["status"], "INVALID_INPUT")
                self.assertEqual(result["authority_effect"], "NONE")

    def test_charter_rejects_malformed_typed_roles(self):
        result = check_charter_contract({field: [] for field in CHARTER_FIELDS})
        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertTrue(any("role binding" in error for error in result["errors"]))

    def test_pecan_rejects_invalid_types_and_dates(self):
        value = {field: {} for field in PECAN_FIELDS}
        value["crossing_id"] = 12
        value["observed_at"] = "not-a-date"
        result = check_pecan_crossing(value)
        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertTrue(any("crossing_id" in error for error in result["errors"]))

    def test_pea_rejects_missing_external_grant_and_reasons(self):
        value = {field: {} for field in PEA_FIELDS}
        result = explain_pea_candidate(value)
        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertTrue(any("external_evaluator_grant" in error for error in result["errors"]))
        self.assertTrue(any("sourced_reasons" in error for error in result["errors"]))

    def test_seed_rejects_untyped_claims_and_choice(self):
        value = {field: [] for field in SEED_FIELDS}
        result = review_seed_release(value)
        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertTrue(any("claims" in error for error in result["errors"]))
        self.assertTrue(any("human_choice" in error for error in result["errors"]))

    def test_peaches_wrapper_rejects_duplicate_and_oversized_integer(self):
        duplicate = _peaches_prepare('{"request_id":"a","request_id":"b"}')
        self.assertEqual(duplicate["status"], "INVALID_INPUT")
        oversized = _peaches_prepare(json.dumps({"n": 10**40}))
        self.assertEqual(oversized["status"], "INVALID_INPUT")

    def test_mcp_review_entrypoint_never_raises_on_malformed_json(self):
        result = _review("{not-json", review_pal_packet)
        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertEqual(result["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()
