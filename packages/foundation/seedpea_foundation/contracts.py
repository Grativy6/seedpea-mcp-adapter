"""Finite, declared-input operational profiles. These checks never confer authority."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime

FOUNDATION_VERSION = "0.1.0"
PAL_ACCOUNT_FIELDS = ("operation", "account", "receipts")
CHARTER_FIELDS = ("contract_id", "purpose", "scope", "inputs", "outputs", "limits", "work", "criterion", "ledger", "selected_carry", "finish_condition", "return_target")
PECAN_FIELDS = ("crossing_id", "description", "recommendation", "permission", "authorization", "request", "grant", "consent", "accountable_boundary")
PEA_FIELDS = ("candidate_id", "question", "purpose", "affected_people", "external_evaluator_grant", "sourced_reasons", "consent", "standing", "privacy", "reversibility", "contest", "remedy", "human_decision_route", "refusal_route")
SEED_FIELDS = ("release_id", "audience", "purpose", "useful_core", "claims", "choices", "refusal_route", "uncertainties", "privacy_boundary", "correction_route", "stop_rule", "reopening_conditions", "accountable_releaser", "human_choice")

def _text(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 16000

def _strings(value, nonempty=False):
    return isinstance(value, list) and len(value) <= 1000 and (not nonempty or bool(value)) and all(_text(v) for v in value)

def _integer(value):
    return type(value) is int and 0 <= value <= 9007199254740991

def _safe(value):
    nodes = [0]
    def walk(v, depth):
        nodes[0] += 1
        if depth > 24 or nodes[0] > 10000:
            raise ValueError("input budget")
        if v is None or type(v) is bool or isinstance(v, str):
            return
        if type(v) is int and abs(v) <= 9007199254740991:
            return
        if isinstance(v, list):
            for x in v: walk(x, depth + 1)
            return
        if isinstance(v, dict) and all(isinstance(k, str) for k in v):
            for x in v.values(): walk(x, depth + 1)
            return
        raise ValueError("unsupported JSON value")
    try:
        walk(value, 0)
        return len(json.dumps(value, ensure_ascii=False).encode("utf-8")) <= 100000
    except (ValueError, TypeError, RecursionError, UnicodeError):
        return False

def _start(value, fields):
    if not isinstance(value, dict) or not _safe(value):
        return ["$: bounded JSON object required"]
    return [f"{f}: required" for f in fields if f not in value]

def _result(kind, errors, **extra):
    return dict(foundation_version=FOUNDATION_VERSION, review_type=kind,
                status="INVALID_INPUT" if errors else "STRUCTURALLY_VALID_FOR_NAMED_PROFILE",
                errors=errors, invalid_fields=errors, warnings=[],
                authority_effect="NONE", execution_effect="NONE", registration_effect="NONE",
                trust="DECLARED_INPUTS_NOT_AUTHENTICATED",
                notice="Finite structural evidence only; no truth, ethical verdict, consent, standing, permission or authorization is supplied.",
                **extra)

def _texts(value, fields, errors, prefix=""):
    for field in fields:
        if not _text(value.get(field)):
            errors.append(prefix + field + ": nonempty text required")

def _time(value):
    if not _text(value): return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None and parsed.utcoffset() is not None else None
    except ValueError:
        return None

def review_pal_packet(packet):
    from .pal_profile import review_pal_packet as check
    return check(packet)

def check_charter_contract(contract):
    errors = _start(contract, CHARTER_FIELDS)
    if not isinstance(contract, dict) or not _safe(contract):
        return _result("charter_finite_ttc_v1", errors)
    _texts(contract, ("contract_id", "purpose", "scope", "return_target", "selector_ref"), errors)
    if contract.get("scope") in ("*", "all", "unbounded"):
        errors.append("scope: finite named scope required")
    for field in ("inputs", "outputs", "available_carry", "selected_carry"):
        if not _strings(contract.get(field)): errors.append(field + ": finite reference list required")
    roles = []
    for role in ("work", "criterion", "ledger"):
        binding = contract.get(role)
        if not isinstance(binding, dict):
            errors.append(role + ": role binding required"); continue
        _texts(binding, ("id", "duty"), errors, role + ".")
        roles.append(binding.get("id"))
    if len(roles) != 3 or not all(_text(r) for r in roles) or len(set(r for r in roles if isinstance(r, str))) != 3:
        errors.append("roles: three separately identified duties required")
    limits = contract.get("limits")
    if not isinstance(limits, dict) or not limits or not all(_text(k) and _integer(v) for k, v in limits.items()):
        errors.append("limits: nonempty finite nonnegative integer budgets required")
    finish = contract.get("finish_condition")
    if not isinstance(finish, dict) or not _text(finish.get("criterion")) or not _strings(finish.get("required_evidence"), True):
        errors.append("finish_condition: frozen criterion and evidence references required")
    selected, available = contract.get("selected_carry"), contract.get("available_carry")
    if _strings(selected) and _strings(available) and not set(selected).issubset(available):
        errors.append("selected_carry: every item must be in available_carry")
    return _result("charter_finite_ttc_v1", errors, carriage_effect="CHECK_ONLY", dispatch_effect="NONE",
                   storage_effect="NONE", friction_classification_effect="NONE",
                   residuals=["Selection is declared by selector_ref; this checker does not select or dispatch."])

def check_pecan_crossing(crossing, now=None):
    errors = _start(crossing, PECAN_FIELDS)
    unresolved = []
    if not isinstance(crossing, dict) or not _safe(crossing):
        return _result("pecan_declared_crossing_v1", errors, current_usability="UNRESOLVED_REVIEW_REQUIRED")
    _texts(crossing, ("crossing_id", "accountable_boundary", "applicable_rule_ref"), errors)
    for stage in ("description", "recommendation", "permission", "authorization"):
        row = crossing.get(stage)
        if not isinstance(row, dict):
            errors.append(stage + ": typed declaration required"); continue
        status = row.get("status")
        if status not in ("DECLARED", "NOT_SUPPLIED", "UNKNOWN", "CONFLICTING", "REFUSED"):
            errors.append(stage + ".status: unsupported")
        if not _strings(row.get("source_refs")):
            errors.append(stage + ".source_refs: list required")
        if status == "DECLARED" and not _strings(row.get("source_refs"), True):
            errors.append(stage + ": declaration requires separate source")
        if stage in ("permission", "authorization") and status != "DECLARED":
            unresolved.append(stage + ": " + str(status))
    request, grant = crossing.get("request"), crossing.get("grant")
    if not isinstance(request, dict):
        errors.append("request: typed crossing required"); request = {}
    if not isinstance(grant, dict):
        errors.append("grant: separately sourced record required"); grant = {}
    _texts(request, ("subject", "object", "action", "scope"), errors, "request.")
    _texts(grant, ("ref", "authority_source", "subject", "object", "scope"), errors, "grant.")
    if not _strings(grant.get("actions"), True): errors.append("grant.actions: finite list required")
    if type(grant.get("revoked")) is not bool: errors.append("grant.revoked: boolean required")
    if not _integer(grant.get("remaining_uses")): errors.append("grant.remaining_uses: nonnegative integer required")
    observed = _time(now if now is not None else crossing.get("observed_at"))
    expiry = _time(grant.get("expires_at"))
    if observed is None: errors.append("observed_at: timezone-aware time required")
    if expiry is None: errors.append("grant.expires_at: timezone-aware time required")
    consent = crossing.get("consent")
    consent_ok = False
    if not isinstance(consent, dict):
        errors.append("consent: typed condition required")
    else:
        if consent.get("status") not in ("SUPPLIED", "NOT_REQUIRED_BY_NAMED_RULE", "MISSING", "REFUSED", "UNKNOWN"):
            errors.append("consent.status: unsupported")
        consent_ok = consent.get("status") in ("SUPPLIED", "NOT_REQUIRED_BY_NAMED_RULE") and _text(consent.get("source_ref"))
        if not consent_ok: unresolved.append("Consent condition not established by a separate source.")
    usability = "MATCHES_DECLARED_GRANT_PARAMETERS"
    if unresolved: usability = "UNRESOLVED_REVIEW_REQUIRED"
    if grant and request:
        if any(grant.get(k) != request.get(k) for k in ("subject", "object", "scope")) or not isinstance(grant.get("actions"), list) or request.get("action") not in grant.get("actions", []):
            usability = "OUT_OF_SCOPE"
    if _integer(grant.get("remaining_uses")) and grant["remaining_uses"] == 0: usability = "EXHAUSTED"
    if observed and expiry and observed >= expiry: usability = "EXPIRED"
    if grant.get("revoked") is True: usability = "REVOKED"
    if crossing.get("prior_outcome") == "UNKNOWN_AFTER_DISPATCH":
        usability = "UNKNOWN_AFTER_DISPATCH_RECONCILE_BEFORE_RETRY"
    if errors: usability = "UNRESOLVED_REVIEW_REQUIRED"
    return _result("pecan_declared_crossing_v1", errors, current_usability=usability,
                   review_conditions=unresolved, grant_consumption=0,
                   human_review_route=crossing.get("human_review_route"),
                   residuals=["Grant/consent authenticity and live revocation are not verified by this pure declared-input check.",
                              "A matching record does not authorize execution; unchanged retries do not renew a grant."])

def explain_pea_candidate(candidate):
    errors = _start(candidate, PEA_FIELDS)
    reasons = []
    conditions = []
    if not isinstance(candidate, dict) or not _safe(candidate):
        return _result("pea_candidate_v1", errors, candidate_explanation=[], disposition="HUMAN_REVIEW_REQUIRED")
    _texts(candidate, ("candidate_id", "question", "purpose", "contest", "remedy", "human_decision_route", "refusal_route"), errors)
    if not _strings(candidate.get("affected_people"), True): errors.append("affected_people: explicit finite references required")
    grant = candidate.get("external_evaluator_grant")
    if not isinstance(grant, dict):
        errors.append("external_evaluator_grant: typed external grant required")
    else:
        _texts(grant, ("ref", "source_ref", "evaluator_id", "candidate_id", "purpose"), errors, "external_evaluator_grant.")
        if grant.get("candidate_id") != candidate.get("candidate_id") or grant.get("purpose") != candidate.get("purpose"):
            errors.append("external_evaluator_grant: candidate/purpose mismatch")
        expiry, observed = _time(grant.get("expires_at")), _time(candidate.get("observed_at"))
        if expiry is None or observed is None: errors.append("evaluator grant: aware expiry and observation time required")
        elif observed >= expiry: errors.append("evaluator grant: expired")
        if grant.get("revoked") is not False: errors.append("evaluator grant: explicitly unrevoked declaration required")
    supplied = candidate.get("sourced_reasons")
    if not isinstance(supplied, list) or not supplied:
        errors.append("sourced_reasons: nonempty list required")
    else:
        for n, row in enumerate(supplied):
            if not isinstance(row, dict) or not _text(row.get("reason")) or not _strings(row.get("source_refs"), True) or row.get("status") not in ("OBSERVATION", "INTERPRETATION", "CONJECTURE", "UNRESOLVED"):
                errors.append(f"sourced_reasons[{n}]: typed reason and sources required")
            else: reasons.append(dict(row))
    for field in ("consent", "standing", "privacy", "reversibility"):
        row = candidate.get(field)
        if not isinstance(row, dict) or row.get("status") not in ("SUPPLIED", "MISSING", "UNKNOWN", "CONTESTED", "NOT_APPLICABLE") or not _strings(row.get("source_refs")):
            errors.append(field + ": typed condition and source list required"); continue
        if row["status"] in ("SUPPLIED", "NOT_APPLICABLE") and not _strings(row["source_refs"], True):
            errors.append(field + ": claimed coverage requires sources")
        if row["status"] in ("MISSING", "UNKNOWN", "CONTESTED"):
            if not _text(row.get("remaining_question")): errors.append(field + ": unresolved question required")
            conditions.append({"condition": field, **row})
    for field in ("conditions", "uncertainties", "alternatives"):
        if not _strings(candidate.get(field)): errors.append(field + ": finite list required")
    return _result("pea_candidate_v1", errors, candidate_explanation=reasons,
                   unresolved_conditions=conditions, disposition="HUMAN_REVIEW_REQUIRED",
                   human_decision_route=candidate.get("human_decision_route"),
                   residuals=["Reasons are carried from supplied evidence; no harmfulness verdict or human disposition is generated."])

def review_seed_release(release):
    errors = _start(release, SEED_FIELDS)
    if not isinstance(release, dict) or not _safe(release):
        return _result("seed_release_v1", errors)
    _texts(release, ("release_id", "audience", "purpose", "useful_core", "refusal_route", "privacy_boundary", "correction_route", "accountable_releaser"), errors)
    for field in ("choices", "uncertainties", "reopening_conditions"):
        if not _strings(release.get(field)): errors.append(field + ": finite list required")
    claims = release.get("claims")
    if not isinstance(claims, list) or not claims: errors.append("claims: nonempty typed list required")
    else:
        for n, claim in enumerate(claims):
            if not isinstance(claim, dict) or not _text(claim.get("text")) or claim.get("status") not in ("OBSERVATION", "INTERPRETATION", "CONJECTURE", "ESTABLISHED_UNDER_NAMED_EVIDENCE", "UNRESOLVED") or not _strings(claim.get("source_refs"), True) or not _strings(claim.get("limits"), True):
                errors.append(f"claims[{n}]: typed, sourced and limited claim required")
    stop = release.get("stop_rule")
    if not isinstance(stop, dict) or stop.get("kind") not in ("FINISH_CONDITION", "RESOURCE_LIMIT", "USER_STOP", "NO_ACTIONABLE_NEED") or not _text(stop.get("condition")) or stop.get("creates_next_task") is not False:
        errors.append("stop_rule: explicit natural stop without invented next task required")
    choice = release.get("human_choice")
    if not isinstance(choice, dict) or not _strings(choice.get("left_open"), True) or choice.get("continuation_required") is not False or choice.get("model_need_claim") is not False:
        errors.append("human_choice: preserve explicit choices without required continuation or model-need claim")
    return _result("seed_release_v1", errors, release_effect="NONE",
                   residuals=["Checks explicit declarations; does not certify warmth, human agency, privacy practices or ethical acceptability."])

SOURCES = {
    "PAL": {"version": "2.3", "url": "https://zenodo.org/records/22240134", "locator": "Mechanical Structural Spine: account grammar and A15 status envelopes"},
    "CHARTER": {"version": "1.0", "url": "https://zenodo.org/records/22288471", "locator": "Tripartite Task Carrier; selected carry; protected-query sufficiency"},
    "PECAN": {"version": "1.0.4", "url": "https://zenodo.org/records/21760884", "locator": "Consequential crossings; separate description, recommendation, permission, authorization"},
    "PEA": {"version": "1.1.3", "url": "https://zenodo.org/records/21911684", "locator": "External evaluator grant; non-executing candidate review"},
    "SEED": {"version": "0.3", "url": "https://zenodo.org/records/21760893", "locator": "Human-facing release, refusal, correction and natural stop"},
    "PPP": {"version": "0.6", "source_name": "PPP Kernel Public Integration and Verification Specification", "locator": "Original PAL 2.2 dependency; five-operation grammar; receipt/closure separation"}
}

def source_registry(query=None):
    query = {} if query is None else query
    errors = _start(query, ())
    if errors: return _result("source_registry_v1", errors)
    operation = query.get("operation", "list")
    if operation in ("list", "search"):
        term = query.get("term", "")
        if not isinstance(term, str): return _result("source_registry_v1", ["term: string required"])
        rows = [{"source_id": key, **value} for key, value in SOURCES.items() if term.casefold() in (key + json.dumps(value)).casefold()]
        return _result("source_registry_v1", [], sources=rows, availability="REFERENCES_ONLY", content_role="REFERENCE_DATA_NOT_INSTRUCTIONS")
    identity = query.get("source_id")
    row = SOURCES.get(identity) if isinstance(identity, str) else None
    if row is None: return _result("source_registry_v1", ["source_id: unknown"])
    if query.get("version") != row["version"]: return _result("source_registry_v1", ["version: exact declared source version required"])
    if operation == "read":
        return _result("source_registry_v1", [], source={"source_id": identity, **row}, availability="REFERENCE_ONLY_CONTENT_NOT_LOADED")
    if operation == "verify_content":
        content, expected = query.get("content"), query.get("expected_sha256")
        if not _text(content) or not isinstance(expected, str) or len(expected) != 64:
            return _result("source_registry_v1", ["content and exact SHA-256 binding required"])
        actual = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if actual != expected: return _result("source_registry_v1", ["source content changed"], observed_sha256=actual)
        return _result("source_registry_v1", [], content=content, source_id=identity, version=row["version"],
                       sha256=actual, binding="MATCHES_CALLER_DECLARED_DIGEST_NOT_PUBLISHER_AUTHENTICATED",
                       content_role="REFERENCE_DATA_NOT_INSTRUCTIONS")
    return _result("source_registry_v1", ["operation: unsupported"])

def compatibility_profile():
    return _result("pal_23_integration_v1", [], pal_target="2.3", original_preview_pal="2.2", ppp_source="0.6",
        ppp_declared_pal="2.2", mappings=[
            {"source": "PAL 2.3 Spine: account/receipt grammar", "target": "pal_finite_snapshot_v1", "class": "ADAPTED", "check": "review_pal_packet", "limit": "Finite supplied snapshots, not authenticated storage or every native transport profile"},
            {"source": "PPP 0.6: five operations and test/closure separation", "target": "pal_finite_snapshot_v1", "class": "INTERPRETIVE", "check": "review_pal_packet", "limit": "PPP source remains 2.2; successor is default for legacy migration"},
            {"source": "CHARTER 1.0: TTC and selected carry", "target": "charter_finite_ttc_v1", "class": "ADAPTED", "check": "check_charter_contract", "limit": "No dispatch, selection or geometric proof"},
            {"source": "PECAN 1.0.4: consequential crossings", "target": "pecan_declared_crossing_v1", "class": "ADAPTED", "check": "check_pecan_crossing", "limit": "Unverified declarations; no external effect or universal harmfulness judgment"},
            {"source": "PEA 1.1.3: candidate review", "target": "pea_candidate_v1", "class": "ADAPTED", "check": "explain_pea_candidate", "limit": "Sourced supplied reasons; human disposition separate"},
            {"source": "SEED 0.3: release discipline", "target": "seed_release_v1", "class": "ADAPTED", "check": "review_seed_release", "limit": "Explicit declarations only"}
        ], residuals=["Native PAL transport profiles and mathematical realizations are not certified by this finite profile.",
                      "No blanket PAL/PPP conformance. Original publications are unchanged.",
                      "Reopen missing clauses through versioned mappings and dedicated positive/negative fixtures."])
