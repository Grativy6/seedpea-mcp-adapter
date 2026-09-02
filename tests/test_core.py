import unittest

from seedpea_adapter.core import (
    GRANT_FIELDS,
    INSTITUTIONAL_REGISTRATION_FIELDS,
    MAX_INPUT_CHARS,
    RELEASE_FIELDS,
    inspect_authority_separation,
    review_evaluator_grant,
    review_institutional_branch_registration,
    review_json,
    review_release_envelope,
    status_manifest,
)


def complete(fields):
    return {field: f"declared:{field}" for field in fields}


class EvaluatorGrantTests(unittest.TestCase):
    def test_complete_grant_is_only_complete_for_review(self):
        grant = complete(GRANT_FIELDS)
        grant["adopted_pea_version"] = "1.1.3"

        result = review_evaluator_grant(grant)

        self.assertEqual(result["status"], "COMPLETE_FOR_REVIEW")
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertEqual(result["execution_effect"], "NONE")
        self.assertEqual(result["registration_effect"], "NONE")
        self.assertNotIn("PASS", result.values())

    def test_missing_grant_field_stays_visible(self):
        grant = complete(GRANT_FIELDS)
        del grant["contest"]

        result = review_evaluator_grant(grant)

        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["missing_fields"], ["contest"])

    def test_version_difference_opens_warning(self):
        grant = complete(GRANT_FIELDS)
        grant["adopted_pea_version"] = "1.1.2"

        result = review_evaluator_grant(grant)

        self.assertTrue(any("migration review" in warning for warning in result["warnings"]))


class ReleaseEnvelopeTests(unittest.TestCase):
    def test_release_requires_stop_and_reopening_routes(self):
        release = complete(RELEASE_FIELDS)
        release["stop_rule"] = ""

        result = review_release_envelope(release)

        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["invalid_fields"], ["stop_rule"])
        self.assertEqual(result["authority_effect"], "NONE")


class AuthoritySeparationTests(unittest.TestCase):
    def test_collapsed_statuses_create_warning_not_authority(self):
        crossing = {
            "description": "declared description",
            "recommendation_status": "present",
            "permission_status": "present",
            "authorization_status": "present",
            "authorization_source": "declared source",
            "scope": "declared scope",
            "expiry": "declared expiry",
            "refusal_route": "declared route",
            "accountable_boundary": "declared institution",
        }

        result = inspect_authority_separation(crossing)

        self.assertEqual(result["status"], "COMPLETE_FOR_REVIEW")
        self.assertTrue(any("collapsed" in warning for warning in result["warnings"]))
        self.assertEqual(result["authority_effect"], "NONE")


class InstitutionalBranchRegistrationTests(unittest.TestCase):
    def test_complete_registration_is_only_complete_for_review(self):
        registration = complete(INSTITUTIONAL_REGISTRATION_FIELDS)
        registration["responsible_human_roles"] = ["accountable owner"]
        registration["authorized_operators"] = ["authorized operator"]

        result = review_institutional_branch_registration(registration)

        self.assertEqual(result["status"], "COMPLETE_FOR_REVIEW")
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertEqual(result["execution_effect"], "NONE")

    def test_responsible_human_roles_must_remain_visible(self):
        registration = complete(INSTITUTIONAL_REGISTRATION_FIELDS)
        registration["responsible_human_roles"] = []
        registration["authorized_operators"] = ["authorized operator"]

        result = review_institutional_branch_registration(registration)

        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["invalid_fields"], ["responsible_human_roles"])

    def test_roles_and_operators_are_non_empty_string_lists(self):
        registration = complete(INSTITUTIONAL_REGISTRATION_FIELDS)
        registration["responsible_human_roles"] = ["review owner"]
        registration["authorized_operators"] = "every employee"

        result = review_institutional_branch_registration(registration)

        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["invalid_fields"], ["authorized_operators"])

    def test_affected_people_and_exit_routes_are_required(self):
        for field in (
            "affected_people_boundary",
            "affected_people_refusal_route",
            "consent_dependencies",
            "correction_route",
            "contest",
            "remedy_route",
            "revocation",
        ):
            with self.subTest(field=field):
                registration = complete(INSTITUTIONAL_REGISTRATION_FIELDS)
                registration["responsible_human_roles"] = ["accountable owner"]
                registration["authorized_operators"] = ["authorized operator"]
                registration[field] = ""

                result = review_institutional_branch_registration(registration)

                self.assertEqual(result["status"], "INCOMPLETE")
                self.assertEqual(result["invalid_fields"], [field])

    def test_registration_review_does_not_echo_declarations(self):
        registration = complete(INSTITUTIONAL_REGISTRATION_FIELDS)
        registration["responsible_human_roles"] = ["private-role-identifier"]
        registration["authorized_operators"] = ["private-operator-identifier"]

        result = review_institutional_branch_registration(registration)

        self.assertNotIn("private-role-identifier", str(result))
        self.assertNotIn("private-operator-identifier", str(result))


class StatusTests(unittest.TestCase):
    def test_manifest_is_explicitly_non_executing(self):
        manifest = status_manifest()

        self.assertEqual(manifest["status"], "PUBLIC_PREVIEW")
        self.assertEqual(manifest["effects"]["authority"], "NONE")
        self.assertEqual(manifest["effects"]["execution"], "NONE")
        self.assertEqual(manifest["effects"]["registration"], "NONE")


class JsonBoundaryTests(unittest.TestCase):
    def test_malformed_json_is_rejected_without_echoing_input(self):
        raw = '{"private_note": "do not repeat"'

        result = review_json(raw, review_evaluator_grant)

        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertNotIn("do not repeat", str(result))
        self.assertEqual(result["authority_effect"], "NONE")

    def test_oversized_json_is_rejected_before_parsing(self):
        raw = " " * (MAX_INPUT_CHARS + 1)

        result = review_json(raw, review_release_envelope)

        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertTrue(any("exceeds" in warning for warning in result["warnings"]))

    def test_extreme_numeric_literal_is_rejected_without_echoing_input(self):
        raw = '{"private_number": ' + ("9" * 5_000) + "}"

        result = review_json(raw, review_evaluator_grant)

        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertNotIn("999999999999", str(result))
        self.assertEqual(result["authority_effect"], "NONE")

    def test_duplicate_keys_are_rejected(self):
        raw = '{"scope": "first", "scope": "second"}'

        result = review_json(raw, review_evaluator_grant)

        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertTrue(any("Duplicate" in warning for warning in result["warnings"]))
        self.assertNotIn("first", str(result))
        self.assertNotIn("second", str(result))

    def test_nonfinite_numbers_are_rejected(self):
        result = review_json('{"scope": NaN}', review_evaluator_grant)

        self.assertEqual(result["status"], "INVALID_INPUT")
        self.assertTrue(any("Non-finite" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
