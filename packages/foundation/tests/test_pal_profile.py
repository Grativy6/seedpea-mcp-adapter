from copy import deepcopy

from seedpea_foundation.pal_profile import review_pal_packet


def account(account_id="acct-root", version=1, kind="ROOT", origin="r-cut"):
    return {
        "account_id": account_id,
        "account_kind": kind,
        "version": version,
        "pal_version": "2.3",
        "origin_cut_id": origin,
        "scope": {"kind": "finite", "name": "fixture"},
        "authority_ceiling": {"execution": "none", "decision": "human"},
    }


def cut(account_id="acct-root", origin="r-cut", links=None):
    return {
        "header": {
            "receipt_id": "r-cut",
            "receipt_type": "CutReceipt",
            "schema_id": "PAL-Receipt",
            "schema_version": 1,
            "account_ref": account_id,
            "origin_cut_ref": origin,
            "admission_order": 1,
            "links": links or {},
        },
        "payload": {"claim": "a bounded distinction", "witness_ref": "source-fixture", "admission_obligation": "review-source", "status": "OPEN"},
    }


def test_root_opening_cut_is_finite_structural_result():
    result = review_pal_packet({"operation": "ROOT", "account": account(), "receipts": [cut()]})
    assert result["status"] == "STRUCTURALLY_VALID_FOR_NAMED_PROFILE"
    assert result["authority_effect"] == "NONE"
    assert result["conformance"] == "FINITE_ADAPTATION_ONLY"


def test_mutated_header_account_and_duplicate_id_are_rejected():
    packet = {"operation": "ROOT", "account": account(), "receipts": [cut()]}
    packet["receipts"].append(deepcopy(packet["receipts"][0]))
    packet["receipts"][1]["header"]["admission_order"] = 2
    result = review_pal_packet(packet)
    assert result["status"] == "INVALID_INPUT"
    assert any("unique" in error["message"] for error in result["errors"])


def test_child_requires_exact_parent_links_and_version_one():
    child = account("acct-child", 1, "CHILD", "cut-child")
    packet = {"operation": "CHILD", "account": child, "prior": {"account_id": "acct-root", "receipt_id": "r-cut"}, "receipts": [cut("acct-child", "cut-child")]}
    result = review_pal_packet(packet)
    assert result["status"] == "INVALID_INPUT"
    assert any("parent references" in error["message"] for error in result["errors"])


def test_append_preserves_prefix_and_adds_exactly_one_receipt():
    prior_receipts = [cut()]
    added = {
        "header": {"receipt_id": "r-occ", "receipt_type": "OccurrenceReceipt", "schema_id": "PAL-Receipt", "schema_version": 1, "account_ref": "acct-root", "origin_cut_ref": "r-cut", "admission_order": 2, "links": {}},
        "payload": {"observation": "retained"},
    }
    packet = {"operation": "APPEND", "account": account(), "prior": {**account(), "receipts": deepcopy(prior_receipts)}, "receipts": prior_receipts + [added]}
    assert review_pal_packet(packet)["status"] == "STRUCTURALLY_VALID_FOR_NAMED_PROFILE"
    packet["receipts"][0]["payload"]["claim"] = "changed"
    assert review_pal_packet(packet)["status"] == "INVALID_INPUT"


def test_version_requires_delta_and_keeps_identity_and_origin():
    prior = {"account_id": "acct-root", "version": 1, "origin_cut_id": "r-cut", "receipts": [cut()]}
    newer = account(version=2)
    transition = {"header": {"receipt_id": "r-transition", "receipt_type": "AccountTransitionReceipt", "schema_id": "PAL-Transition", "schema_version": 1, "account_ref": "acct-root", "origin_cut_ref": "r-cut", "admission_order": 2, "links": {}}, "payload": {"delta": {"kind": "typed-transition", "reason": "profile update"}}}
    packet = {"operation": "VERSION", "account": newer, "prior": prior, "receipts": [cut(), transition], "delta": {"kind": "typed-transition", "reason": "profile update"}}
    result = review_pal_packet(packet)
    assert result["status"] == "STRUCTURALLY_VALID_FOR_NAMED_PROFILE"
    packet["receipts"].pop()
    assert review_pal_packet(packet)["status"] == "INVALID_INPUT"


def test_test_receipt_does_not_become_closure_and_needs_both_check_kinds():
    receipt = {"header": {"receipt_id": "r-test", "receipt_type": "TestReceipt", "schema_id": "PAL-Test", "schema_version": 1, "account_ref": "acct-root", "origin_cut_ref": "r-cut", "admission_order": 2, "links": {}}, "payload": {"verdict": "CONFORMANT", "checks": [{"kind": "positive", "result": "PASS"}], "closure_status": "CLOSED_IN_SCOPE"}}
    result = review_pal_packet({"operation": "APPEND", "account": account(), "prior": {"account_id": "acct-root", "version": 1, "receipts": [cut()]}, "receipts": [cut(), receipt]})
    assert result["status"] == "INVALID_INPUT"
    assert any("negative" in error["message"] for error in result["errors"])
    assert any("TestReceipt cannot" in error["message"] for error in result["errors"])


def test_closed_closure_requires_separate_passing_test_and_completeness_boundary():
    test = {"header": {"receipt_id": "r-test", "receipt_type": "TestReceipt", "schema_id": "PAL-Test", "schema_version": 1, "account_ref": "acct-root", "origin_cut_ref": "r-cut", "admission_order": 2, "links": {}}, "payload": {"verdict": "CONFORMANT", "checks": [{"kind": "positive", "result": "PASS", "evidence_ref": "ev-pos"}, {"kind": "negative", "result": "PASS", "evidence_ref": "ev-neg"}]}}
    closure = {"header": {"receipt_id": "r-close", "receipt_type": "ClosureReceipt", "schema_id": "PAL-Closure", "schema_version": 1, "account_ref": "acct-root", "origin_cut_ref": "r-cut", "admission_order": 3, "links": {}}, "payload": {"claim": "closed locally", "scope": {"name": "fixture"}, "dependency_versions": {"fixture": "1"}, "evidence": ["r-test"], "decision_rule": "finite", "tolerance": {"kind": "none"}, "resource_profile": {"kind": "test"}, "authority_ceiling": {"execution": "none", "decision": "human"}, "snapshot": {"source": "fixture"}, "stable_residuals": [], "reopening": {"handle": "reopen-1"}, "status": "CLOSED_IN_SCOPE", "open_obligations": [], "scope_completeness_boundary": "all named fixture checks", "test_receipt_refs": ["r-test"]}}
    packet = {"operation": "ROOT", "account": account(), "receipts": [cut(), test, closure]}
    assert review_pal_packet(packet)["status"] == "STRUCTURALLY_VALID_FOR_NAMED_PROFILE"
    del closure["payload"]["scope_completeness_boundary"]
    assert review_pal_packet(packet)["status"] == "INVALID_INPUT"


def test_malformed_untrusted_input_is_reported_without_exception():
    class NotJson:
        pass
    result = review_pal_packet(NotJson())
    assert result["status"] == "INVALID_INPUT"
    assert result["authority_effect"] == "NONE"


def test_reopen_requires_prior_closure_and_material_delta():
    packet = {"operation": "REOPEN", "account": account(), "prior": {"account_id": "acct-root", "version": 1, "receipts": [cut()]}, "receipts": [cut()]}
    result = review_pal_packet(packet)
    assert result["status"] == "INVALID_INPUT"
    assert any("material delta" in error["message"] for error in result["errors"])


def test_root_must_start_at_version_one():
    result = review_pal_packet({"operation": "ROOT", "account": account(version=2), "receipts": [cut()]})
    assert result["status"] == "INVALID_INPUT"
    assert any("ROOT accounts" in error["message"] for error in result["errors"])


def test_unhashable_discriminators_are_invalid_not_exceptions():
    packet = {"operation": [], "account": account(), "receipts": [cut()]}
    packet["account"]["account_kind"] = []
    result = review_pal_packet(packet)
    assert result["status"] == "INVALID_INPUT"


def test_unsupported_receipt_type_is_explicit_profile_residual():
    unsupported = {"header": {"receipt_id": "r-opaque", "receipt_type": "OpaqueFutureReceipt", "schema_id": "future", "schema_version": 1, "account_ref": "acct-root", "origin_cut_ref": "r-cut", "admission_order": 2, "links": {}}, "payload": {"opaque": "kept"}}
    result = review_pal_packet({"operation": "ROOT", "account": account(), "receipts": [cut(), unsupported]})
    assert result["status"] == "UNSUPPORTED_PROFILE"
    assert result["authority_effect"] == "NONE"


def test_legacy_wrapper_and_residual_require_lineage_fields():
    legacy = {"header": {"receipt_id": "r-legacy", "receipt_type": "LegacyReceiptRef", "schema_id": "legacy", "schema_version": 1, "account_ref": "acct-root", "origin_cut_ref": "r-cut", "admission_order": 2, "links": {}}, "payload": {"legacy_source_id": "PAL-2.2", "raw_bytes_hash": "hash", "wrapper_receipt_id": "wrong"}}
    residual = {"header": {"receipt_id": "r-residual", "receipt_type": "ResidualReceipt", "schema_id": "PAL-Residual", "schema_version": 1, "account_ref": "acct-root", "origin_cut_ref": "r-cut", "admission_order": 3, "links": {}}, "payload": {"stable_residual_id": "res-1"}}
    result = review_pal_packet({"operation": "ROOT", "account": account(), "receipts": [cut(), legacy, residual]})
    assert result["status"] == "INVALID_INPUT"
    assert any("legacy wrapper" in error["message"] for error in result["errors"])
    assert any("residual receipt" in error["message"] for error in result["errors"])


def test_pal_2_2_prior_cannot_be_relabelled_as_version_update():
    prior = {**account(), "pal_version": "2.2", "receipts": [cut()]}
    result = review_pal_packet({"operation": "VERSION", "account": account(version=2), "prior": prior, "receipts": [cut()], "delta": {"kind": "transition"}})
    assert result["status"] == "INVALID_INPUT"
    assert any("SUCCESSOR" in error["message"] for error in result["errors"])
