"""Deterministic, read-only SeedPEA boundary checks.

These helpers inspect whether declared review packets contain the fields
needed for later accountable review. They do not evaluate truth, ethics,
permission, authorization, compliance, or execution readiness.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any


ADAPTER_VERSION = "0.1.0"
MAX_INPUT_CHARS = 100_000

CONTROLLING_SOURCES = {
    "PAL": "2.2",
    "PECAN": "1.0.4",
    "PEA Core": "1.1.3",
    "SEED": "0.3",
}

GRANT_FIELDS = (
    "grant_id",
    "grantor",
    "adopted_pea_version",
    "scope",
    "admitted_inputs",
    "data_access",
    "permitted_outputs",
    "operational_role",
    "retention",
    "contest",
    "expiry",
    "revocation",
    "lineage",
    "accountable_boundary",
)

RELEASE_FIELDS = (
    "release_id",
    "audience",
    "purpose",
    "requested_support",
    "claim_status",
    "sources",
    "uncertainties",
    "privacy",
    "retention",
    "correction_route",
    "contest_route",
    "stop_rule",
    "reopening_conditions",
    "accountable_releaser",
)

AUTHORITY_FIELDS = (
    "description",
    "recommendation_status",
    "permission_status",
    "authorization_status",
    "authorization_source",
    "scope",
    "expiry",
    "refusal_route",
    "accountable_boundary",
)

INSTITUTIONAL_REGISTRATION_FIELDS = (
    "registration_id",
    "branch_id",
    "institution_identity",
    "institution_authority_source",
    "responsible_human_roles",
    "authorized_operators",
    "scope",
    "purpose",
    "affected_people_boundary",
    "affected_people_refusal_route",
    "consent_dependencies",
    "data_access",
    "retention",
    "correction_route",
    "contest",
    "remedy_route",
    "expiry",
    "revocation",
    "lineage",
    "accountable_boundary",
)


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _base_result(review_type: str) -> dict[str, Any]:
    return {
        "adapter_version": ADAPTER_VERSION,
        "review_type": review_type,
        "authority_effect": "NONE",
        "execution_effect": "NONE",
        "registration_effect": "NONE",
        "notice": (
            "Structural completeness is not truth, recommendation, permission, "
            "authorization, ethical approval, legal compliance, or an accountable decision."
        ),
    }


class _JsonBoundaryError(ValueError):
    """A safe-to-report JSON boundary violation."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _JsonBoundaryError("Duplicate object keys are not accepted.")
        result[key] = value
    return result


def _reject_nonfinite_number(value: str) -> None:
    del value
    raise _JsonBoundaryError("Non-finite numeric values are not accepted.")


def review_json(raw: str, reviewer: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
    """Parse a bounded JSON object and pass it to a deterministic reviewer."""

    if not isinstance(raw, str):
        result = _base_result("input_parse")
        result.update(
            {
                "status": "INVALID_INPUT",
                "missing_fields": [],
                "invalid_fields": ["$"],
                "warnings": ["Input must be a JSON string."],
            }
        )
        return result

    if len(raw) > MAX_INPUT_CHARS:
        result = _base_result("input_parse")
        result.update(
            {
                "status": "INVALID_INPUT",
                "missing_fields": [],
                "invalid_fields": ["$"],
                "warnings": [f"Input exceeds the {MAX_INPUT_CHARS}-character preview limit."],
            }
        )
        return result

    try:
        payload = json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite_number,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        if isinstance(exc, json.JSONDecodeError):
            detail = exc.msg
        elif isinstance(exc, RecursionError):
            detail = "JSON nesting is too deep."
        elif isinstance(exc, _JsonBoundaryError):
            detail = str(exc)
        else:
            detail = "A numeric value is outside the accepted JSON boundary."
        result = _base_result("input_parse")
        result.update(
            {
                "status": "INVALID_INPUT",
                "missing_fields": [],
                "invalid_fields": ["$"],
                "warnings": [f"Input must be valid bounded JSON: {detail}"],
            }
        )
        return result

    return reviewer(payload)


def _review_required_fields(
    payload: Any,
    required_fields: tuple[str, ...],
    review_type: str,
) -> dict[str, Any]:
    result = _base_result(review_type)

    if not isinstance(payload, Mapping):
        result.update(
            {
                "status": "INVALID_INPUT",
                "missing_fields": list(required_fields),
                "invalid_fields": ["$"],
                "warnings": ["Input must be a JSON object."],
            }
        )
        return result

    missing = [field for field in required_fields if field not in payload]
    blank = [
        field
        for field in required_fields
        if field in payload and _is_blank(payload[field])
    ]

    result.update(
        {
            "status": "COMPLETE_FOR_REVIEW" if not missing and not blank else "INCOMPLETE",
            "missing_fields": missing,
            "invalid_fields": blank,
            "warnings": [],
        }
    )
    return result


def review_evaluator_grant(grant: Any) -> dict[str, Any]:
    """Check the declared field boundary of a PEA evaluator grant."""

    result = _review_required_fields(grant, GRANT_FIELDS, "evaluator_grant")
    if not isinstance(grant, Mapping):
        return result

    adopted = grant.get("adopted_pea_version")
    if not _is_blank(adopted) and str(adopted) != CONTROLLING_SOURCES["PEA Core"]:
        result["warnings"].append(
            "The declared PEA version differs from the adapter's reviewed PEA Core 1.1.3 boundary. "
            "A versioned compatibility or migration review remains open."
        )

    return result


def review_release_envelope(release: Any) -> dict[str, Any]:
    """Check a human-facing release declaration against a minimum public boundary."""

    return _review_required_fields(release, RELEASE_FIELDS, "release_envelope")


def inspect_authority_separation(crossing: Any) -> dict[str, Any]:
    """Check that description, recommendation, permission, and authorization are explicit."""

    result = _review_required_fields(crossing, AUTHORITY_FIELDS, "authority_separation")
    if not isinstance(crossing, Mapping):
        return result

    statuses = {
        "recommendation_status": crossing.get("recommendation_status"),
        "permission_status": crossing.get("permission_status"),
        "authorization_status": crossing.get("authorization_status"),
    }
    reused_values = {
        str(value).strip().casefold()
        for value in statuses.values()
        if not _is_blank(value)
    }
    if len(reused_values) == 1 and len(statuses) == 3:
        result["warnings"].append(
            "Recommendation, permission, and authorization use the same declared status. "
            "Confirm that no transition was inferred or collapsed."
        )

    return result


def review_institutional_branch_registration(registration: Any) -> dict[str, Any]:
    """Check the declared boundary of a branch held by an institution."""

    result = _review_required_fields(
        registration,
        INSTITUTIONAL_REGISTRATION_FIELDS,
        "institutional_branch_registration",
    )
    if not isinstance(registration, Mapping):
        return result

    for field in ("responsible_human_roles", "authorized_operators"):
        value = registration.get(field)
        if field not in registration or _is_blank(value):
            continue
        if not isinstance(value, list) or any(
            not isinstance(item, str) or _is_blank(item) for item in value
        ):
            result["invalid_fields"].append(field)

    result["invalid_fields"] = list(dict.fromkeys(result["invalid_fields"]))
    if result["missing_fields"] or result["invalid_fields"]:
        result["status"] = "INCOMPLETE"

    return result


def status_manifest() -> dict[str, Any]:
    """Return the adapter's declared identity and non-claims."""

    return {
        "name": "SeedPEA MCP Adapter",
        "adapter_version": ADAPTER_VERSION,
        "status": "PUBLIC_PREVIEW",
        "controlling_sources": CONTROLLING_SOURCES,
        "effects": {
            "network": "NONE",
            "filesystem": "NONE",
            "shell": "NONE",
            "credentials": "NONE",
            "authority": "NONE",
            "execution": "NONE",
            "registration": "NONE",
        },
        "non_claims": [
            "No specification-conformance claim",
            "No ethical approval",
            "No legal or regulatory compliance certification",
            "No consent, permission, jurisdiction, or authorization",
            "No autonomous institutional decision",
            "No branch, account, role, or operator registration",
            "No ownership, rights, consent, or authority transfer",
        ],
    }
