from seedpea_foundation.pal24_profile import review_pal24_resources, review_pal24_resume
import hashlib
import json


def binding(source_id="pal", version="2.4", digest=None, content="source"):
    if digest is None:
        raw = json.dumps(content, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
        digest = "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
    row = {"source_id": source_id, "version": version, "expected_hash": digest}
    if content is not None:
        row["content"] = content
    return row


def resume_packet():
    checkpoint = {
        "checkpoint_id": "cp-1",
        "work_state": {"cursor": 4, "pending": ["e5"]},
        "task_version": "task-1",
        "admitted_suffix": ["e1", "e2"],
        "source_bindings": [binding()],
        "requirements": [{"requirement_id": "r1", "field": "mode", "equals": "safe", "evidence_refs": ["ev1"]}],
        "task_id": "task-1", "projection_id": "projection-1", "transition_ref": "transition-1",
        "observation_ref": "observation-1", "horizon": "POINTWISE",
    }
    observed = dict(checkpoint)
    observed["source_bindings"] = [binding()]
    return {
        "operation": "RESUME",
        "checkpoint": checkpoint,
        "observed": observed,
        "current": {"facts": {"mode": {"value": "safe", "evidence_refs": ["ev1"]}}, "grant": {"status": "ACTIVE"}, "resources": {"status": "AVAILABLE"}},
        "claims": {"exact_work_recovery": True, "continuation_equivalence": True, "scope": "POINTWISE"},
    }


def resource_packet(events=None, complete=True):
    return {
        "root": {
            "node_id": "root", "unit": "tokens", "epoch": "e1", "boundary": "job-1",
            "complete": complete, "events": events or [{"event_id": "a", "amount": 3, "owner": "root", "parent_exclusive": True}],
            "children": [], "expected_child_ids": [],
        },
        "declared_total": 3,
    }


def test_resume_checks_exact_work_separately_from_other_predicates():
    result = review_pal24_resume(resume_packet())
    assert result["status"] == "STRUCTURALLY_VALID_FOR_NAMED_PROFILE"
    assert result["predicates"]["exact_work_recovery"] == "PASS"
    assert result["predicates"]["source_identity"] == "MATCH"
    assert result["predicates"]["continuation_equivalence"] == "NOT_ASSESSED"
    assert result["authority_effect"] == "NONE"


def test_resume_does_not_turn_changed_work_into_answer_or_continuation():
    packet = resume_packet()
    packet["observed"]["work_state"] = {"cursor": 5, "pending": ["e5"]}
    result = review_pal24_resume(packet)
    assert result["status"] == "UNRESOLVED"
    assert result["predicates"]["exact_work_recovery"] == "FAIL"
    assert result["predicates"]["selected_answer"] == "NOT_ASSESSED"
    assert result["predicates"]["continuation_equivalence"] == "NOT_ASSESSED"


def test_resume_keeps_unknown_applicability_and_expired_grant_open():
    packet = resume_packet()
    packet["observed"]["source_bindings"] = [binding(content="different")]
    packet["current"]["grant"] = {"status": "EXPIRED"}
    result = review_pal24_resume(packet)
    assert result["status"] == "UNRESOLVED"
    assert result["predicates"]["current_grant"] == "EXPIRED"
    assert result["predicates"]["source_content"] == "MISMATCH"


def test_resume_requires_successor_for_changed_requirements():
    packet = resume_packet()
    packet["observed"]["requirements"] = []
    result = review_pal24_resume(packet)
    assert result["status"] == "UNRESOLVED"
    assert result["predicates"]["current_applicability"] == "MISMATCH"
    packet["successor_record"] = {"prior_ref": "cp-1", "adoption_ref": "successor-1"}
    result = review_pal24_resume(packet)
    assert result["status"] == "UNRESOLVED"


def test_resources_accept_unique_parent_exclusive_events():
    result = review_pal24_resources(resource_packet())
    assert result["status"] == "STRUCTURALLY_VALID_FOR_NAMED_PROFILE"
    assert result["accounting"]["known_total"] == 3


def test_resources_reject_duplicate_event_and_unit_mismatch():
    packet = resource_packet(events=[{"event_id": "a", "amount": 1, "owner": "root"}])
    packet["root"]["children"] = [{
        "node_id": "child", "parent_id": "root", "unit": "seconds", "epoch": "e1", "boundary": "job-1",
        "complete": True, "events": [{"event_id": "a", "amount": 2, "owner": "child"}], "children": [],
    }]
    packet["declared_total"] = 3
    result = review_pal24_resources(packet)
    assert result["status"] == "INVALID_INPUT"
    assert any("event_id" in error["field"] for error in result["errors"])
    assert any(error["field"] == "root.children[0]" for error in result["errors"])


def test_resources_keep_unknown_cost_unknown_and_incomplete():
    packet = resource_packet(events=[{"event_id": "a", "amount": "UNKNOWN", "owner": "root"}], complete=False)
    packet.pop("declared_total")
    result = review_pal24_resources(packet)
    assert result["status"] == "UNRESOLVED"
    assert result["accounting"]["unknown_cost"] is True
    assert result["accounting"]["known_total"] == 0
    assert result["accounting"]["total"] is None
    assert any("not zero" in residual for residual in result["residuals"])


def test_resources_reject_missing_complete_child():
    packet = resource_packet()
    packet["root"]["expected_child_ids"] = ["child"]
    result = review_pal24_resources(packet)
    assert result["status"] == "INVALID_INPUT"


def test_resources_allow_parent_exclusive_event_on_intermediate_node():
    packet = resource_packet()
    packet["root"]["complete"] = False
    packet["root"]["children"] = [{
        "node_id": "child", "parent_id": "root", "unit": "tokens", "epoch": "e1", "boundary": "job-1",
        "complete": True, "events": [{"event_id": "b", "amount": 2, "owner": "child", "parent_exclusive": True}],
        "children": [], "expected_child_ids": [],
    }]
    result = review_pal24_resources(packet)
    assert not any("parent_exclusive" in error["field"] for error in result["errors"])
