"""Adversarial boundaries for the PAL 2.4 finite adapter.

These tests intentionally describe the contract that the production checker
must satisfy.  They use synthetic packets only and never invoke a model or a
runtime authority.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from seedpea_foundation.pal24 import review_pal24_resources, review_pal24_resume


def canonical_digest(value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


SOURCE = {"id": "source", "version": 1, "content": {"text": "bound"}}


def source_row(content=SOURCE["content"], version="2.4", source_id="pal"):
    return {"source_id": source_id, "version": version, "content": content}


def requirement(field="mode", value="safe", refs=None, requirement_id="r1"):
    row = {"requirement_id": requirement_id, "field": field, "equals": value, "evidence_refs": ["ev1"] if refs is None else refs}
    return row


def resume_packet():
    digest = canonical_digest(SOURCE["content"])
    frozen_source = {"source_id": "pal", "version": "2.4", "expected_hash": digest}
    observed_source = source_row()
    checkpoint = {
        "checkpoint_id": "cp-1", "work_state": {"cursor": 1}, "task_version": "task-v1",
        "task_id": "task-1", "projection_id": "projection-1", "transition_ref": "transition-1",
        "observation_ref": "observation-1", "horizon": "POINTWISE", "admitted_suffix": ["e1"],
        "source_bindings": [frozen_source], "requirements": [requirement()],
    }
    observed = dict(checkpoint)
    observed["source_bindings"] = [observed_source]
    return {
        "operation": "RESUME", "checkpoint": checkpoint, "observed": observed,
        "current": {"facts": {"mode": {"value": "safe", "evidence_refs": ["ev1"]}},
                     "grant": {"status": "ACTIVE"}, "resources": {"status": "AVAILABLE"}},
    }


def resource_packet(**overrides):
    root = {
        "node_id": "root", "unit": "tokens", "epoch": "e1", "boundary": "b1",
        "complete": True, "expected_child_ids": [], "events": [], "children": [],
    }
    root.update(overrides.pop("root", {}))
    packet = {"root": root, "declared_total": overrides.pop("declared_total", 0)}
    packet.update(overrides)
    return packet


def test_resume_extra_observed_source_is_unresolved_without_exception():
    packet = resume_packet()
    packet["observed"]["source_bindings"].append(source_row(source_id="extra"))
    result = review_pal24_resume(packet)
    assert result["status"] in {"UNRESOLVED", "INVALID_INPUT"}
    assert result["predicates"]["source_identity"] == "MISMATCH"


def test_resume_missing_source_content_is_unknown_not_verified():
    packet = resume_packet()
    packet["observed"]["source_bindings"][0].pop("content")
    result = review_pal24_resume(packet)
    assert result["predicates"]["source_content"] == "UNKNOWN"
    assert result["status"] in {"INVALID_INPUT", "UNRESOLVED"}


def test_resume_wrong_source_version_and_hash_are_mismatch():
    packet = resume_packet()
    packet["observed"]["source_bindings"][0]["version"] = "wrong"
    packet["observed"]["source_bindings"][0]["content"] = {"text": "altered"}
    result = review_pal24_resume(packet)
    assert result["predicates"]["source_identity"] == "MISMATCH"
    assert result["predicates"]["source_content"] == "MISMATCH"


def test_resume_missing_equals_is_invalid_even_without_facts():
    packet = resume_packet()
    packet["checkpoint"]["requirements"][0].pop("equals")
    packet["observed"]["requirements"] = [requirement()]
    packet["observed"]["requirements"][0].pop("equals")
    packet["current"].pop("facts")
    result = review_pal24_resume(packet)
    assert result["status"] == "INVALID_INPUT"


@pytest.mark.parametrize("refs", [[], [""]])
def test_resume_empty_requirement_refs_do_not_pass(refs):
    packet = resume_packet()
    packet["checkpoint"]["requirements"][0]["evidence_refs"] = refs
    packet["observed"]["requirements"][0]["evidence_refs"] = refs
    result = review_pal24_resume(packet)
    assert result["predicates"]["current_applicability"] == "UNKNOWN"
    assert result["status"] in {"INVALID_INPUT", "UNRESOLVED"}


def test_resume_empty_fact_refs_are_unknown():
    packet = resume_packet()
    packet["current"]["facts"]["mode"]["evidence_refs"] = []
    result = review_pal24_resume(packet)
    assert result["predicates"]["current_applicability"] == "UNKNOWN"


def test_resume_known_mismatch_survives_later_unknown_fact():
    packet = resume_packet()
    packet["checkpoint"]["requirements"] = [requirement("mode", "required"), requirement("other", "x", requirement_id="r2")]
    packet["observed"]["requirements"] = packet["checkpoint"]["requirements"]
    packet["current"]["facts"] = {"mode": {"value": "wrong", "evidence_refs": ["ev1"]}}
    result = review_pal24_resume(packet)
    assert result["predicates"]["current_applicability"] == "MISMATCH"


def test_resume_duplicate_requirement_ids_are_invalid():
    packet = resume_packet()
    packet["checkpoint"]["requirements"].append(requirement("other", "x"))
    packet["observed"]["requirements"] = packet["checkpoint"]["requirements"]
    result = review_pal24_resume(packet)
    assert result["status"] == "INVALID_INPUT"


def test_resume_bool_and_int_are_distinct():
    packet = resume_packet()
    packet["checkpoint"]["requirements"][0] = requirement("flag", True)
    packet["observed"]["requirements"][0] = requirement("flag", True)
    packet["current"]["facts"] = {"flag": {"value": 1, "evidence_refs": ["ev1"]}}
    result = review_pal24_resume(packet)
    assert result["predicates"]["current_applicability"] == "MISMATCH"


@pytest.mark.parametrize("field", ["reset", "topup", "top_up", "reset_ref", "topup_ref"])
def test_resources_reject_unsupported_reset_or_topup(field):
    result = review_pal24_resources(resource_packet(root={field: 1}))
    assert result["status"] == "INVALID_INPUT"


def test_resources_unknown_amount_and_declared_zero_remain_unknown():
    result = review_pal24_resources(resource_packet(root={"events": [{"event_id": "e", "amount": "UNKNOWN", "owner": "root"}]}, declared_total=0))
    assert result["status"] == "UNRESOLVED"
    assert result["accounting"]["unknown_cost"] is True
    assert result["accounting"]["known_total"] == 0
    assert result["accounting"]["total"] is None


def test_resources_complete_requires_child_manifest():
    result = review_pal24_resources(resource_packet(root={"expected_child_ids": None}))
    assert result["status"] == "INVALID_INPUT"


def test_resources_duplicate_child_and_event_ids_are_invalid():
    child = {"node_id": "child", "parent_id": "root", "unit": "tokens", "epoch": "e1", "boundary": "b1",
             "complete": True, "expected_child_ids": [], "events": [{"event_id": "e", "amount": 1, "owner": "child"}], "children": []}
    result = review_pal24_resources(resource_packet(root={"expected_child_ids": ["child", "child"], "children": [child], "events": [{"event_id": "e", "amount": 1, "owner": "root"}]}))
    assert result["status"] == "INVALID_INPUT"


def test_resources_nested_unit_mismatch_is_invalid():
    child = {"node_id": "child", "parent_id": "root", "unit": "seconds", "epoch": "e1", "boundary": "b1",
             "complete": True, "expected_child_ids": [], "events": [], "children": []}
    result = review_pal24_resources(resource_packet(root={"expected_child_ids": ["child"], "children": [child]}))
    assert result["status"] == "INVALID_INPUT"


def test_resources_cyclic_or_repeated_ids_are_invalid():
    child = {"node_id": "root", "parent_id": "root", "unit": "tokens", "epoch": "e1", "boundary": "b1",
             "complete": True, "expected_child_ids": [], "events": [], "children": []}
    result = review_pal24_resources(resource_packet(root={"expected_child_ids": ["root"], "children": [child]}))
    assert result["status"] == "INVALID_INPUT"


def test_resources_nested_budget_bound_is_invalid_input_not_exception():
    packet = resource_packet()
    node = packet["root"]
    for index in range(30):
        child = {"node_id": f"n{index}", "parent_id": node["node_id"], "unit": "tokens", "epoch": "e1", "boundary": "b1",
                 "complete": True, "expected_child_ids": [], "events": [], "children": []}
        node["complete"] = False
        node["expected_child_ids"] = [child["node_id"]]
        node["children"] = [child]
        node = child
    result = review_pal24_resources(packet)
    assert result["status"] == "INVALID_INPUT"


@pytest.mark.parametrize("current", [{"grant": {"status": {} }}, {"grant": {"status": []}}, {"resources": {"status": {}}}])
def test_resume_malformed_enum_values_are_invalid_not_exception(current):
    packet = resume_packet()
    packet["current"] = current
    result = review_pal24_resume(packet)
    assert result["status"] == "INVALID_INPUT"


@pytest.mark.parametrize("scope", [{}, []])
def test_resume_malformed_claim_scope_is_invalid_not_exception(scope):
    packet = resume_packet()
    packet["claims"] = {"scope": scope}
    result = review_pal24_resume(packet)
    assert result["status"] == "INVALID_INPUT"
