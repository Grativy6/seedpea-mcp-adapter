"""Finite, bounded PAL 2.3 operational profile.

This module is an executable adapter profile, not a PAL conformance claim.  It
checks a deliberately finite account/receipt language and reports the parts of
the source contract which are represented.  It never authenticates a caller,
creates authority, or treats a successful check as substantive closure.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

MAX_BYTES = 100_000
MAX_DEPTH = 24
MAX_NODES = 10_000
PROFILE = "PAL-2.3-finite-account-receipt-profile"


def _base(status: str, errors: list[str] | None = None, warnings: list[str] | None = None,
          residuals: list[str] | None = None) -> dict[str, Any]:
    return {
        "profile": PROFILE,
        "status": status,
        "errors": errors or [],
        "warnings": warnings or [],
        "residuals": residuals or [],
        "authority_effect": "NONE",
        "execution_effect": "NONE",
        "registration_effect": "NONE",
        "conformance": "FINITE_ADAPTATION_ONLY",
        "notice": "This result is scoped evidence for review; it is not truth, permission, authorization, ethics, standing, or closure outside the declared profile.",
    }


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
        if isinstance(node, (str, int, bool)) or node is None:
            return True, ""
        if isinstance(node, Mapping):
            for key, child in node.items():
                if not isinstance(key, str):
                    return False, "mapping keys must be strings"
                ok, reason = walk(child, depth + 1)
                if not ok:
                    return ok, reason
            return True, ""
        if isinstance(node, Sequence) and not isinstance(node, (bytes, bytearray)):
            for child in node:
                ok, reason = walk(child, depth + 1)
                if not ok:
                    return ok, reason
            return True, ""
        return False, "value is not JSON-like"
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        encoded_bytes = encoded.encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError, OverflowError):
        return False, "input is not bounded JSON"
    if len(encoded_bytes) > MAX_BYTES:
        return False, "input exceeds byte bound"
    try:
        return walk(value, 0)
    except (RecursionError, UnicodeError):
        return False, "input cannot be traversed within bounds"


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _aware(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _same_ref(value: Any, account: Mapping[str, Any], name: str) -> bool:
    return isinstance(value, str) and value == account.get(name)


def _typed_links(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    return all(isinstance(key, str) and (v is None or _text(v) or (isinstance(v, list) and all(_text(x) for x in v))) for key, v in value.items())


def _safe_equal(left: Any, right: Any) -> bool:
    try:
        return left == right
    except Exception:
        return False


def _immutable_account_fields(account: Mapping[str, Any]) -> dict[str, Any]:
    return {key: account.get(key) for key in ("account_kind", "version", "pal_version", "origin_cut_id", "scope", "authority_ceiling")}


def _error(result: dict[str, Any], field: str, message: str) -> None:
    result["errors"].append({"field": field, "message": message})


def _check_header(header: Any, account: Mapping[str, Any], expected_order: int,
                  seen: set[str], result: dict[str, Any]) -> bool:
    if not isinstance(header, Mapping):
        _error(result, "header", "receipt header must be a mapping")
        return False
    required = ("receipt_id", "receipt_type", "schema_id", "schema_version", "account_ref", "origin_cut_ref", "admission_order")
    ok = True
    for field in required:
        if field not in header:
            _error(result, "header." + field, "required immutable header field is missing")
            ok = False
    rid = header.get("receipt_id")
    if not _text(rid) or rid in seen:
        _error(result, "header.receipt_id", "receipt IDs must be non-empty and unique")
        ok = False
    else:
        seen.add(rid)
    if not _text(header.get("receipt_type")):
        _error(result, "header.receipt_type", "receipt type must be named")
        ok = False
    if not _text(header.get("schema_id")) or not _integer(header.get("schema_version")):
        _error(result, "header.schema", "schema identity and integer version are required")
        ok = False
    if not _same_ref(header.get("account_ref"), account, "account_id"):
        _error(result, "header.account_ref", "receipt must bind to its account")
        ok = False
    origin = header.get("origin_cut_ref")
    if not (_text(origin) and origin == account.get("origin_cut_id")):
        _error(result, "header.origin_cut_ref", "receipt must bind to the account origin cut")
        ok = False
    if header.get("admission_order") != expected_order:
        _error(result, "header.admission_order", "admission order must be contiguous and immutable")
        ok = False
    links = header.get("links", {})
    if not _typed_links(links):
        _error(result, "header.links", "typed links must be a mapping")
        ok = False
    return ok


def _check_receipts(account: Mapping[str, Any], receipts: Any, result: dict[str, Any]) -> tuple[bool, list[Mapping[str, Any]]]:
    if not isinstance(receipts, list):
        _error(result, "receipts", "receipts must be an ordered list")
        return False, []
    seen: set[str] = set()
    valid = True
    normalized: list[Mapping[str, Any]] = []
    for order, receipt in enumerate(receipts, 1):
        if not isinstance(receipt, Mapping):
            _error(result, f"receipts[{order - 1}]", "receipt must be a mapping")
            valid = False
            continue
        header = receipt.get("header")
        if not _check_header(header, account, order, seen, result):
            valid = False
        if "payload" not in receipt or not isinstance(receipt.get("payload"), Mapping):
            _error(result, f"receipts[{order - 1}].payload", "receipt payload must be a mapping")
            valid = False
        else:
            normalized.append(receipt)
        if receipt.get("correction_of") is not None and not _text(receipt.get("correction_of")):
            _error(result, f"receipts[{order - 1}].correction_of", "correction links must be typed receipt IDs")
            valid = False
    return valid, normalized


def _account_valid(account: Any, result: dict[str, Any]) -> bool:
    if not isinstance(account, Mapping):
        _error(result, "account", "account must be a mapping")
        return False
    required = ("account_id", "account_kind", "version", "pal_version", "origin_cut_id", "scope", "authority_ceiling")
    valid = True
    for field in required:
        if field not in account:
            _error(result, "account." + field, "required account field is missing")
            valid = False
    if not _text(account.get("account_id")) or not isinstance(account.get("account_kind"), str) or account.get("account_kind") not in {"ROOT", "CHILD", "SUCCESSOR"}:
        _error(result, "account.identity", "account identity and kind must be typed")
        valid = False
    if not _integer(account.get("version")) or account.get("version", 0) < 1:
        _error(result, "account.version", "account version must be a positive integer")
        valid = False
    if account.get("pal_version") != "2.3":
        _error(result, "account.pal_version", "this finite profile requires PAL 2.3 records")
        valid = False
    if not _text(account.get("origin_cut_id")) or not isinstance(account.get("scope"), Mapping) or not isinstance(account.get("authority_ceiling"), Mapping):
        _error(result, "account.boundary", "origin, scope, and authority ceiling must be explicit")
        valid = False
    return valid


def _first_cut(account: Mapping[str, Any], receipt: Mapping[str, Any], result: dict[str, Any]) -> bool:
    header = receipt.get("header", {})
    payload = receipt.get("payload", {})
    valid = header.get("receipt_type") == "CutReceipt" and header.get("admission_order") == 1
    if not valid:
        _error(result, "opening_cut", "an account must open with one CutReceipt")
    if payload.get("status") != "OPEN":
        _error(result, "opening_cut.status", "the opening cut must remain OPEN")
        valid = False
    if not _text(payload.get("claim")) or not _text(payload.get("witness_ref")) or not _text(payload.get("admission_obligation")):
        _error(result, "opening_cut.payload", "opening cut requires a claim, witness reference, and admission obligation")
        valid = False
    if payload.get("witness_ref") in ("OMEGA", "Ω", "self"):
        _error(result, "opening_cut.witness_ref", "the cut cannot manufacture a self-witness")
        valid = False
    if header.get("receipt_id") != account.get("origin_cut_id"):
        _error(result, "opening_cut.origin", "opening CutReceipt ID must establish the account origin")
        valid = False
    return valid


def _typed_receipt_checks(account: Mapping[str, Any], receipts: list[Mapping[str, Any]], result: dict[str, Any]) -> None:
    for index, receipt in enumerate(receipts):
        header = receipt.get("header", {})
        payload = receipt.get("payload", {})
        kind = header.get("receipt_type")
        if kind == "TestReceipt":
            verdict = payload.get("verdict")
            if not isinstance(verdict, str) or verdict not in {"CONFORMANT", "NONCONFORMANT"}:
                _error(result, f"receipts[{index}].payload.verdict", "test verdict must be CONFORMANT or NONCONFORMANT")
            if verdict == "CONFORMANT":
                checks = payload.get("checks")
                valid_checks = isinstance(checks, list) and all(isinstance(c, Mapping) and _text(c.get("kind")) and c.get("result") == "PASS" and _text(c.get("evidence_ref")) for c in checks)
                if not valid_checks or not any(c.get("kind") == "positive" for c in checks) or not any(c.get("kind") == "negative" for c in checks):
                    _error(result, f"receipts[{index}].payload.checks", "CONFORMANT requires independent passing positive and negative checks")
            if payload.get("closure_status") is not None or payload.get("claim_status") is not None:
                _error(result, f"receipts[{index}].payload", "TestReceipt cannot carry closure or claim status")
        elif kind == "ClosureReceipt":
            required = ("claim", "scope", "dependency_versions", "evidence", "decision_rule", "tolerance", "resource_profile", "authority_ceiling", "snapshot", "stable_residuals", "reopening", "status")
            for field in required:
                if field not in payload:
                    _error(result, f"receipts[{index}].payload.{field}", "closure envelope field is required")
            status = payload.get("status")
            if not isinstance(status, str) or status not in {"CLOSED_IN_SCOPE", "OPEN", "UNRESOLVED", "REOPENED"}:
                _error(result, f"receipts[{index}].payload.status", "closure status is not a declared PAL status")
            if status == "CLOSED_IN_SCOPE":
                if payload.get("open_obligations") != []:
                    _error(result, f"receipts[{index}].payload.open_obligations", "scoped closure cannot retain open obligations")
                if not payload.get("scope_completeness_boundary"):
                    _error(result, f"receipts[{index}].payload.scope_completeness_boundary", "closure must state its completeness boundary")
                refs = payload.get("test_receipt_refs")
                prior_pass = isinstance(refs, list) and all(_text(ref) for ref in refs) and any(r.get("header", {}).get("receipt_id") in refs and r.get("header", {}).get("receipt_type") == "TestReceipt" and r.get("payload", {}).get("verdict") == "CONFORMANT" for r in receipts[:index])
                if not prior_pass:
                    _error(result, f"receipts[{index}].payload.test_receipt_refs", "closure needs a separate prior passing TestReceipt")
                if not isinstance(payload.get("scope"), Mapping) or not payload.get("scope"):
                    _error(result, f"receipts[{index}].payload.scope", "closure scope must be non-empty")
                if not isinstance(payload.get("authority_ceiling"), Mapping) or not _safe_equal(payload.get("authority_ceiling"), account.get("authority_ceiling")):
                    _error(result, f"receipts[{index}].payload.authority_ceiling", "closure cannot widen the account authority ceiling")
            if status == "REOPENED" and not (_text(payload.get("prior_closure_ref")) and isinstance(payload.get("material_delta"), Mapping) and bool(payload.get("material_delta")) and any(r.get("header", {}).get("receipt_id") == payload.get("prior_closure_ref") and r.get("header", {}).get("receipt_type") == "ClosureReceipt" for r in receipts[:index])):
                _error(result, f"receipts[{index}].payload.reopening", "reopened closure requires prior closure and material delta")
        elif kind == "LegacyReceiptRef":
            if not _text(payload.get("legacy_source_id")) or not _text(payload.get("raw_bytes_hash")) or payload.get("wrapper_receipt_id") != header.get("receipt_id"):
                _error(result, f"receipts[{index}].payload", "legacy wrapper must preserve source identity and raw byte hash")
        elif kind == "ResidualReceipt":
            if not _text(payload.get("stable_residual_id")) or not _text(payload.get("transition_identity")) or not isinstance(payload.get("delta"), Mapping):
                _error(result, f"receipts[{index}].payload", "residual receipt requires stable identity, transition identity, and typed delta")
        elif isinstance(kind, str) and kind not in {"CutReceipt", "AccountTransitionReceipt", "OccurrenceReceipt", "TransportReceipt", "ResidualReceipt", "LegacyReceiptRef"}:
            result["residuals"].append(f"unsupported receipt type retained as named residual: {kind}")
            result["status"] = "UNSUPPORTED_PROFILE"


def review_pal_packet(packet: Any) -> dict[str, Any]:
    """Review a finite PAL account packet without conferring authority."""
    bounded, reason = _bounded(packet)
    if not bounded:
        return _base("INVALID_INPUT", [{"field": "$", "message": reason}])
    if not isinstance(packet, Mapping):
        return _base("INVALID_INPUT", [{"field": "$", "message": "packet must be a mapping"}])
    result = _base("STRUCTURALLY_VALID_FOR_NAMED_PROFILE", residuals=["This finite adapter does not establish full PAL 2.3 conformance or validate every native transport/profile."])
    account = packet.get("account")
    if not _account_valid(account, result):
        result["status"] = "INVALID_INPUT"
        return result
    receipts = packet.get("receipts")
    receipts_valid, normalized = _check_receipts(account, receipts, result)
    if not normalized or not _first_cut(account, normalized[0], result):
        receipts_valid = False
    kind = packet.get("operation")
    if not isinstance(kind, str) or kind not in {"ROOT", "CHILD", "SUCCESSOR", "APPEND", "VERSION", "REOPEN"}:
        _error(result, "operation", "operation must be ROOT, CHILD, SUCCESSOR, APPEND, VERSION, or REOPEN")
        receipts_valid = False
    if isinstance(kind, str) and kind in {"CHILD", "SUCCESSOR"}:
        prior = packet.get("prior")
        prior_valid = isinstance(prior, Mapping) and _text(prior.get("account_id")) and _text(prior.get("receipt_id"))
        if not prior_valid:
            _error(result, "prior", "CHILD and SUCCESSOR require exact parent/superseded account and receipt references")
            receipts_valid = False
        if account.get("version") != 1:
            _error(result, "account.version", "new child/successor account must begin at version 1")
            receipts_valid = False
        if normalized and prior_valid and not (normalized[0].get("header", {}).get("links", {}).get("parent_account_ref") == prior.get("account_id") and normalized[0].get("header", {}).get("links", {}).get("parent_receipt_ref") == prior.get("receipt_id")):
            _error(result, "opening_cut.links", "opening cut must bind exact parent references")
            receipts_valid = False
    if kind == "ROOT" and account.get("version") != 1:
        _error(result, "account.version", "ROOT accounts must begin at version 1")
        receipts_valid = False
    if kind == "ROOT" and packet.get("prior") is not None:
        _error(result, "prior", "ROOT cannot have a parent")
        receipts_valid = False
    if isinstance(kind, str) and kind in {"APPEND", "VERSION", "REOPEN"}:
        prior = packet.get("prior")
        if not isinstance(prior, Mapping):
            _error(result, "prior", "continuation requires a prior account snapshot")
            receipts_valid = False
        else:
            if isinstance(kind, str) and kind in {"APPEND", "REOPEN"} and (account.get("account_id") != prior.get("account_id") or account.get("version") != prior.get("version")):
                _error(result, "account.identity", "APPEND/REOPEN must preserve account identity and version")
                receipts_valid = False
            if isinstance(kind, str) and kind in {"APPEND", "REOPEN"} and not _safe_equal(_immutable_account_fields(account), _immutable_account_fields(prior)):
                _error(result, "account.boundary", "APPEND/REOPEN cannot change immutable account scope, origin, version, or authority ceiling")
                receipts_valid = False
            if kind == "VERSION":
                prior_version = prior.get("version")
                if prior.get("pal_version") == "2.2":
                    _error(result, "operation", "PAL 2.2 to 2.3 requires a SUCCESSOR transition unless continuity is independently proven")
                    receipts_valid = False
                if not _integer(prior_version) or account.get("account_id") != prior.get("account_id") or account.get("origin_cut_id") != prior.get("origin_cut_id") or account.get("version") != prior_version + 1:
                    _error(result, "account.version", "VERSION requires same identity/origin and exactly one version increment")
                    receipts_valid = False
                if packet.get("delta") is None or not isinstance(packet.get("delta"), Mapping):
                    _error(result, "delta", "VERSION requires a typed transition delta")
                    receipts_valid = False
            old = prior.get("receipts")
            if isinstance(old, list):
                if len(normalized) < len(old) or [_digest(x) for x in normalized[:len(old)]] != [_digest(x) for x in old]:
                    _error(result, "receipts", "continuation must preserve the immutable prior prefix")
                    receipts_valid = False
                if kind == "APPEND" and len(normalized) != len(old) + 1:
                    _error(result, "receipts", "APPEND adds exactly one receipt")
                    receipts_valid = False
                if kind == "VERSION":
                    if len(normalized) <= len(old):
                        _error(result, "receipts", "VERSION requires a first transition receipt after the preserved prefix")
                        receipts_valid = False
                    else:
                        transition = normalized[len(old)]
                        if transition.get("header", {}).get("receipt_type") != "AccountTransitionReceipt" or not isinstance(transition.get("payload", {}).get("delta"), Mapping) or not _safe_equal(transition.get("payload", {}).get("delta"), packet.get("delta")):
                            _error(result, "receipts", "VERSION first new receipt must be a typed AccountTransitionReceipt carrying the delta")
                            receipts_valid = False
            else:
                _error(result, "prior.receipts", "prior snapshot must carry its immutable receipt prefix")
                receipts_valid = False
    if kind == "REOPEN" and packet.get("delta") is None:
        _error(result, "delta", "REOPEN requires a material delta and retains prior closure history")
        receipts_valid = False
    _typed_receipt_checks(account, normalized, result)
    if result["errors"] or not receipts_valid:
        result["status"] = "INVALID_INPUT"
    result["checked_receipt_count"] = len(normalized)
    result["account_id"] = account.get("account_id")
    return result


__all__ = ["review_pal_packet", "PROFILE"]
