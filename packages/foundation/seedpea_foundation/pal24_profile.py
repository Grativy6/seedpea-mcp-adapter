"""Small, read-only PAL 2.4 continuation and resource profiles.

This is an explicitly finite adaptation of the PAL 2.4 source material.  It
checks declared records; it does not replay code, authenticate sources,
renew grants, establish truth, or claim PAL conformance.  The older PAL 2.3
profile deliberately remains in :mod:`pal_profile`.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import hashlib
import json
import re
from typing import Any

MAX_BYTES = 100_000
MAX_DEPTH = 24
MAX_NODES = 10_000
PROFILE = "PAL-2.4-finite-continuation-resource-profile"
RESUME_PROFILE = "PAL-2.4-finite-resume-v1"
RESOURCE_PROFILE = "PAL-2.4-finite-nested-resource-v1"


def _base(profile: str, status: str = "STRUCTURALLY_VALID_FOR_NAMED_PROFILE") -> dict[str, Any]:
    return {
        "profile": profile,
        "status": status,
        "errors": [],
        "warnings": [],
        "residuals": [],
        "authority_effect": "NONE",
        "execution_effect": "NONE",
        "registration_effect": "NONE",
        "conformance": "FINITE_ADAPTATION_ONLY",
        "trust": "DECLARED_INPUTS_NOT_AUTHENTICATED",
        "notice": "Scoped evidence from declared inputs; not truth, permission, authorization, authenticity, or closure outside this profile.",
    }


def _error(result: dict[str, Any], field: str, message: str) -> None:
    result["errors"].append({"field": field, "message": message})


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _aware(value: Any) -> bool:
    if not _text(value):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _bounded(value: Any) -> tuple[bool, str]:
    count = 0

    def walk(node: Any, depth: int) -> tuple[bool, str]:
        nonlocal count
        count += 1
        if count > MAX_NODES:
            return False, "input exceeds node bound"
        if depth > MAX_DEPTH:
            return False, "input exceeds nesting bound"
        if isinstance(node, float):
            return False, "floating point values are not accepted in PAL records"
        if type(node) is int and abs(node) > 9007199254740991:
            return False, "integer exceeds exact JSON interoperability bound"
        if node is None or isinstance(node, (str, int, bool)):
            return True, ""
        if isinstance(node, Mapping):
            for key, child in node.items():
                if not isinstance(key, str):
                    return False, "mapping keys must be strings"
                ok, why = walk(child, depth + 1)
                if not ok:
                    return False, why
            return True, ""
        if isinstance(node, list):
            for child in node:
                ok, why = walk(child, depth + 1)
                if not ok:
                    return False, why
            return True, ""
        return False, "value is not bounded JSON-like data"

    try:
        ok, why = walk(value, 0)
        if not ok:
            return ok, why
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        if len(raw.encode("utf-8")) > MAX_BYTES:
            return False, "input exceeds byte bound"
        return True, ""
    except (TypeError, ValueError, UnicodeError, RecursionError, OverflowError):
        return False, "input is not bounded JSON"


def _digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _list(value: Any) -> bool:
    return isinstance(value, list)


def _ref_list(value: Any) -> bool:
    return _list(value) and all(_text(item) for item in value)


def _same_json(left: Any, right: Any) -> bool:
    try:
        return _digest(left) == _digest(right)
    except (TypeError, ValueError):
        return False


def _canonical_equal(left: Any, right: Any) -> bool:
    """JSON equality with bool and integer kept as distinct types."""
    if type(left) is not type(right):
        return False
    if isinstance(left, Mapping):
        return set(left) == set(right) and all(_canonical_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_canonical_equal(a, b) for a, b in zip(left, right))
    return left == right


def _source_rows(value: Any, field: str, result: dict[str, Any], *, require_hash: bool = True) -> dict[str, Mapping[str, Any]]:
    rows: dict[str, Mapping[str, Any]] = {}
    if not _list(value):
        _error(result, field, "source bindings must be an ordered list")
        return rows
    for index, row in enumerate(value):
        prefix = f"{field}[{index}]"
        if not isinstance(row, Mapping):
            _error(result, prefix, "source binding must be a mapping")
            continue
        for required in ("source_id", "version"):
            if not _text(row.get(required)):
                _error(result, f"{prefix}.{required}", "required source identity field is missing")
        if require_hash and (not isinstance(row.get("expected_hash"), str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", row.get("expected_hash"))):
            _error(result, f"{prefix}.expected_hash", "expected_hash must be a lowercase sha256: digest")
        source_id = row.get("source_id")
        if not _text(source_id):
            continue
        if source_id in rows:
            _error(result, f"{prefix}.source_id", "source identity must be unique")
        rows[source_id] = row
    return rows


def _source_predicates(checkpoint: Mapping[str, Any], observed: Mapping[str, Any], result: dict[str, Any]) -> dict[str, str]:
    expected = _source_rows(checkpoint.get("source_bindings"), "checkpoint.source_bindings", result, require_hash=True)
    actual = _source_rows(observed.get("source_bindings"), "observed.source_bindings", result, require_hash=False)
    identity = []
    content = []
    if set(actual) - set(expected):
        identity.append("MISMATCH")
    if list(actual) != [key for key in expected if key in actual]:
        identity.append("MISMATCH")
    for key, frozen in expected.items():
        row = actual.get(key)
        if row is None:
            identity.append("UNKNOWN")
            content.append("UNKNOWN")
            continue
        identity.append("MATCH" if frozen.get("version") == row.get("version") else "MISMATCH")
        if "expected_hash" in row and row["expected_hash"] != frozen.get("expected_hash"):
            identity.append("MISMATCH")
        content.append("UNKNOWN" if "content" not in row else
                       "MATCH" if _digest(row["content"]) == frozen.get("expected_hash") else "MISMATCH")
    return {"source_identity": _combined(identity), "source_content": _combined(content)}


def _combined(states):
    return "MISMATCH" if "MISMATCH" in states else "UNKNOWN" if "UNKNOWN" in states else "MATCH"


def _review_requirements(checkpoint: Mapping[str, Any], observed: Mapping[str, Any], current: Mapping[str, Any], result: dict[str, Any]) -> str:
    requirements = checkpoint.get("requirements")
    observed_requirements = observed.get("requirements")
    if not isinstance(requirements, list) or not isinstance(observed_requirements, list):
        _error(result, "requirements", "checkpoint and observed requirements lists are mandatory; an empty list is explicit scope")
        return "UNKNOWN"
    if not _canonical_equal(requirements, observed_requirements):
        result["residuals"].append("Observed obligations differ from the frozen checkpoint; a successor record cannot approve this same-checkpoint resume.")
        return "MISMATCH"
    facts = current.get("facts", {})
    if not isinstance(facts, Mapping):
        _error(result, "current.facts", "facts must be an object")
        facts = {}
    states = []
    seen: set[str] = set()
    for index, requirement in enumerate(requirements):
        prefix = f"checkpoint.requirements[{index}]"
        if not isinstance(requirement, Mapping):
            _error(result, prefix, "requirement must be a mapping")
            states.append("UNKNOWN")
            continue
        for key in ("requirement_id", "field", "equals", "evidence_refs"):
            if key not in requirement:
                _error(result, f"{prefix}.{key}", "required field is missing")
        if not _text(requirement.get("requirement_id")) or not _text(requirement.get("field")) or not _ref_list(requirement.get("evidence_refs")):
            _error(result, prefix, "typed requirement identity, field and evidence list required")
            states.append("UNKNOWN")
            continue
        if requirement["requirement_id"] in seen:
            _error(result, f"{prefix}.requirement_id", "requirement IDs must be unique")
        seen.add(requirement["requirement_id"])
        fact = facts.get(requirement["field"])
        if not isinstance(fact, Mapping) or "value" not in fact or not _ref_list(fact.get("evidence_refs")):
            states.append("UNKNOWN")
            continue
        if not _canonical_equal(requirement.get("equals"), fact.get("value")):
            states.append("MISMATCH")
        elif not requirement["evidence_refs"] or not fact["evidence_refs"] or not set(requirement["evidence_refs"]).issubset(set(fact["evidence_refs"])):
            states.append("UNKNOWN")
    if not requirements:
        result["residuals"].append("No continuation conditions were declared in the explicitly empty requirement scope.")
    return _combined(states)


def _claim_status(value: Any) -> str:
    if value is False or value in (None, "NOT_CLAIMED"):
        return "NOT_CLAIMED"
    return "NOT_ASSESSED"


def review_pal24_resume(packet: Any) -> dict[str, Any]:
    """Review one declared freeze/thaw continuation packet.

    Required shape is ``checkpoint`` and ``observed`` mappings.  Each carries
    ``work_state``, ``task_version``, ``admitted_suffix`` and ``source_bindings``.
    ``current`` may declare grant/resource state.  Work equality is checked
    separately from source, applicability, grant and resource predicates.
    """
    bounded, why = _bounded(packet)
    if not bounded:
        result = _base(RESUME_PROFILE, "INVALID_INPUT")
        _error(result, "$", why)
        return result
    result = _base(RESUME_PROFILE)
    if not isinstance(packet, Mapping):
        _error(result, "$", "resume packet must be a mapping")
        result["status"] = "INVALID_INPUT"
        return result
    if packet.get("operation") != "RESUME":
        _error(result, "operation", "operation must be RESUME")
    checkpoint, observed = packet.get("checkpoint"), packet.get("observed")
    if not isinstance(checkpoint, Mapping):
        _error(result, "checkpoint", "checkpoint mapping is required")
        checkpoint = {}
    if not isinstance(observed, Mapping):
        _error(result, "observed", "observed mapping is required")
        observed = {}
    required = ("work_state", "task_version", "admitted_suffix", "source_bindings", "requirements", "task_id", "projection_id", "transition_ref", "observation_ref", "horizon")
    for name, row in (("checkpoint", checkpoint), ("observed", observed)):
        for field in required:
            if field not in row:
                _error(result, f"{name}.{field}", "required protected-work field is missing")
        if not _text(row.get("task_version")):
            _error(result, f"{name}.task_version", "task version must be named")
        if not _ref_list(row.get("admitted_suffix")):
            _error(result, f"{name}.admitted_suffix", "admitted suffix must be a finite reference list")
        for field in ("task_id", "projection_id", "transition_ref", "observation_ref"):
            if not _text(row.get(field)):
                _error(result, f"{name}.{field}", "continuation contract identity is required")
        if row.get("horizon") != "POINTWISE":
            _error(result, f"{name}.horizon", "this finite profile accepts POINTWISE horizon only")
    if result["errors"]:
        result["status"] = "INVALID_INPUT"
        return result

    work_match = _same_json(checkpoint.get("work_state"), observed.get("work_state"))
    result["predicates"] = {
        "exact_work_recovery": "PASS" if work_match else "FAIL",
        "selected_answer": "NOT_ASSESSED",
        "continuation_equivalence": "NOT_ASSESSED",
        "task_version": "MATCH" if checkpoint.get("task_version") == observed.get("task_version") else "MISMATCH",
        "admitted_suffix": "MATCH" if checkpoint.get("admitted_suffix") == observed.get("admitted_suffix") else "MISMATCH",
    }
    for field in ("task_id", "projection_id", "transition_ref", "observation_ref", "horizon"):
        result["predicates"][field] = "MATCH" if _canonical_equal(checkpoint.get(field), observed.get(field)) else "MISMATCH"
    result["digests"] = {
        "checkpoint_work": _digest(checkpoint.get("work_state")),
        "observed_work": _digest(observed.get("work_state")),
    }
    current = packet.get("current", {})
    if not isinstance(current, Mapping):
        _error(result, "current", "current state must be a mapping")
        current = {}
    result["predicates"].update(_source_predicates(checkpoint, observed, result))
    result["predicates"]["current_applicability"] = _review_requirements(checkpoint, observed, current, result)
    grant = current.get("grant", {})
    if not isinstance(grant, Mapping):
        _error(result, "current.grant", "grant state must be a mapping")
        grant = {}
    grant_status = grant.get("status", "UNKNOWN")
    if not isinstance(grant_status, str) or grant_status not in {"ACTIVE", "EXPIRED", "REVOKED", "UNKNOWN"}:
        _error(result, "current.grant.status", "grant status is unsupported")
        grant_status = "UNKNOWN"
    result["predicates"]["current_grant"] = grant_status
    resources = current.get("resources", {})
    if not isinstance(resources, Mapping):
        _error(result, "current.resources", "resource state must be a mapping")
        resources = {}
    resource_status = resources.get("status", "UNKNOWN")
    if not isinstance(resource_status, str) or resource_status not in {"AVAILABLE", "EXHAUSTED", "UNKNOWN"}:
        _error(result, "current.resources.status", "resource status is unsupported")
        resource_status = "UNKNOWN"
    result["predicates"]["current_resources"] = resource_status
    claims = packet.get("claims", {})
    if not isinstance(claims, Mapping):
        _error(result, "claims", "claims must be a mapping")
    elif isinstance(claims, Mapping):
        result["claims"] = {key: _claim_status(value) for key, value in claims.items() if isinstance(key, str)}
        scope = claims.get("scope")
        if scope is not None and (not isinstance(scope, str) or scope not in {"POINTWISE", "ONE_SUFFIX", "FINITE_HORIZON"}):
            _error(result, "claims.scope", "scope must be POINTWISE, ONE_SUFFIX, or FINITE_HORIZON")
        if isinstance(scope, str) and scope in {"ONE_SUFFIX", "FINITE_HORIZON"}:
            result["residuals"].append("Continuation equivalence requires an independently declared transition and observation contract; this profile does not execute one.")
    if result["errors"]:
        result["status"] = "INVALID_INPUT"
    elif not work_match:
        result["status"] = "UNRESOLVED"
        result["residuals"].append("Protected work did not recover exactly; no answer or continuation claim is inferred.")
    elif any(value in {"MISMATCH", "UNKNOWN", "EXPIRED", "REVOKED", "EXHAUSTED"} for key, value in result["predicates"].items() if key != "exact_work_recovery"):
        result["status"] = "UNRESOLVED"
        result["residuals"].append("Non-work predicates remain distinct and may narrow or prevent resumption; unknown is not pass or zero.")
    return result


def _resource_error(result: dict[str, Any], field: str, message: str) -> None:
    _error(result, field, message)


def review_pal24_resources(packet: Any) -> dict[str, Any]:
    """Review a finite, acyclic nested resource account.

    A tree node has ``node_id``, ``unit``, ``epoch``, ``boundary``,
    ``complete``, ``events`` and ``children``.  Events are unique globally;
    ``parent_exclusive`` events are charged once to their declared owner.
    Unknown amounts remain unknown and cannot be cast to zero.
    """
    bounded, why = _bounded(packet)
    result = _base(RESOURCE_PROFILE)
    if not bounded:
        result["status"] = "INVALID_INPUT"
        _resource_error(result, "$", why)
        return result
    if not isinstance(packet, Mapping):
        result["status"] = "INVALID_INPUT"
        _resource_error(result, "$", "resource packet must be a mapping")
        return result
    root = packet.get("root")
    if set(packet) - {"root", "declared_total"}:
        _resource_error(result, "$", "unsupported resource packet fields")
    if not isinstance(root, Mapping):
        result["status"] = "INVALID_INPUT"
        _resource_error(result, "root", "root resource node is required")
        return result
    seen_nodes: set[str] = set()
    seen_events: set[str] = set()
    total = 0
    unknown = False
    incomplete = False
    root_unit, root_epoch, root_boundary = root.get("unit"), root.get("epoch"), root.get("boundary")

    def visit(node: Mapping[str, Any], path: tuple[str, ...], parent: str | None) -> None:
        nonlocal total, unknown, incomplete
        node_id = node.get("node_id")
        prefix = "root" if not path else "root.children[" + "][".join(path) + "]"
        if not _text(node_id):
            _resource_error(result, prefix + ".node_id", "node identity is required")
            return
        if node_id in seen_nodes:
            _resource_error(result, prefix + ".node_id", "resource tree must be acyclic with unique node IDs")
            return
        seen_nodes.add(node_id)
        if set(node) - {"node_id", "parent_id", "unit", "epoch", "boundary", "complete", "events", "children", "expected_child_ids"}:
            _resource_error(result, prefix, "unsupported node fields; reset/topup mutation is outside this finite profile")
        if parent is not None and node.get("parent_id", parent) != parent:
            _resource_error(result, prefix + ".parent_id", "parent identity does not match the containing node")
        for field in ("unit", "epoch", "boundary"):
            if not _text(node.get(field)):
                _resource_error(result, prefix + "." + field, "unit, epoch, and boundary are required")
        if node.get("unit") != root_unit or node.get("epoch") != root_epoch or node.get("boundary") != root_boundary:
            _resource_error(result, prefix, "nested resource nodes must share the declared unit, epoch, and boundary")
        if type(node.get("complete")) is not bool:
            _resource_error(result, prefix + ".complete", "complete must be an explicit boolean")
        if node.get("complete") is not True:
            incomplete = True
        events = node.get("events")
        if not _list(events):
            _resource_error(result, prefix + ".events", "events must be a list")
            events = []
        for index, event in enumerate(events):
            ep = f"{prefix}.events[{index}]"
            if not isinstance(event, Mapping):
                _resource_error(result, ep, "event must be a mapping")
                continue
            if set(event) - {"event_id", "amount", "owner", "parent_exclusive", "status"}:
                _resource_error(result, ep, "unsupported event fields")
            event_id = event.get("event_id")
            if not _text(event_id) or event_id in seen_events:
                _resource_error(result, ep + ".event_id", "event IDs must be unique")
                continue
            seen_events.add(event_id)
            if event.get("owner") != node_id:
                _resource_error(result, ep + ".owner", "event attribution must identify its owning node")
            if "parent_exclusive" in event and type(event.get("parent_exclusive")) is not bool:
                _resource_error(result, ep + ".parent_exclusive", "parent_exclusive must be boolean")
            amount = event.get("amount")
            event_status = event.get("status", "UNKNOWN" if amount == "UNKNOWN" else "KNOWN")
            if not isinstance(event_status, str) or event_status not in {"KNOWN", "UNKNOWN"}:
                _resource_error(result, ep + ".status", "status must be KNOWN or UNKNOWN")
            elif (event_status == "UNKNOWN") != (amount == "UNKNOWN"):
                _resource_error(result, ep, "amount and status disagree")
            if amount == "UNKNOWN" or event.get("status") == "UNKNOWN":
                unknown = True
            elif not _integer(amount) or amount < 0:
                _resource_error(result, ep + ".amount", "amount must be a nonnegative integer or UNKNOWN")
            else:
                total += amount
        children = node.get("children")
        if not _list(children):
            _resource_error(result, prefix + ".children", "children must be a list")
            children = []
        expected = node.get("expected_child_ids")
        if node.get("complete") is True and expected is None:
            _resource_error(result, prefix + ".expected_child_ids", "complete node requires an explicit child manifest, including []")
        if expected is not None:
            if not _ref_list(expected) or len(set(expected)) != len(expected):
                _resource_error(result, prefix + ".expected_child_ids", "expected child IDs must be a unique reference list")
            elif node.get("complete") is True and {child.get("node_id") for child in children if isinstance(child, Mapping) and _text(child.get("node_id"))} != set(expected):
                _resource_error(result, prefix + ".children", "complete node is missing an in-scope child")
        for index, child in enumerate(children):
            if isinstance(child, Mapping):
                visit(child, path + (str(index),), node_id)
            else:
                _resource_error(result, f"{prefix}.children[{index}]", "child must be a mapping")

    visit(root, (), None)
    declared_total = packet.get("declared_total")
    if declared_total is not None and (not _integer(declared_total) or declared_total < 0):
        _resource_error(result, "declared_total", "declared total must be a nonnegative integer")
    elif declared_total is not None and not unknown and not incomplete and declared_total != total:
        _resource_error(result, "declared_total", "declared total does not equal uniquely attributed event total")
    complete = not incomplete and not result["errors"]
    result["accounting"] = {"known_total": total, "total": total if complete and not unknown else None,
                             "declared_total": declared_total, "unknown_cost": unknown, "complete": complete}
    if result["errors"]:
        result["status"] = "INVALID_INPUT"
    elif unknown or incomplete:
        result["status"] = "UNRESOLVED"
        if unknown:
            result["residuals"].append("Unknown required cost is retained as UNKNOWN; it is not zero and cannot support a complete total.")
        if incomplete:
            result["residuals"].append("The declared tree is incomplete; no completeness follows from a subtotal.")
    return result
