"""FastMCP registration for the shared foundation."""
from __future__ import annotations
from typing import Any
from mcp.types import ToolAnnotations
from .contracts import *
from .legacy import (
    review_json, review_evaluator_grant, review_release_envelope,
    inspect_authority_separation, review_institutional_branch_registration,
)
from peaches_book import prepare_registration, verify_bundle, PeachesError
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
def _bounded_object(raw: str):
    def require_object(value):
        if isinstance(value, dict): return value
        result = {"status":"INVALID_INPUT", "missing_fields":[], "invalid_fields":["$"], "warnings":["Top-level JSON value must be an object."], "authority_effect":"NONE", "execution_effect":"NONE", "registration_effect":"NONE"}
        return result
    return review_json(raw, require_object)
def _review(raw: str, reviewer):
    value = _bounded_object(raw)
    if not isinstance(value, dict) or value.get("status") == "INVALID_INPUT": return value
    try:
        return reviewer(value)
    except Exception as exc:
        return {"status":"INVALID_INPUT", "missing_fields":[], "invalid_fields":["$"], "warnings":[f"Reviewer rejected the bounded input: {type(exc).__name__}."], "authority_effect":"NONE", "execution_effect":"NONE", "registration_effect":"NONE"}
def _peaches_prepare(raw: str, context_raw: str | None = None):
    payload = _bounded_object(raw)
    if not isinstance(payload, dict) or payload.get("status") == "INVALID_INPUT": return payload
    context = _bounded_object(context_raw) if context_raw else None
    if context_raw and (not isinstance(context, dict) or context.get("status") == "INVALID_INPUT"): return context
    try: return {"status":"PREPARED_TEST_REGISTRATION","envelope":prepare_registration(payload, context)}
    except Exception as exc: return {"status":"INVALID_REGISTRATION","error":type(exc).__name__,"authority_effect":"NONE","execution_effect":"NONE"}
def _peaches_verify(raw: str, context_raw: str | None = None):
    bundle = _bounded_object(raw)
    if not isinstance(bundle, dict) or bundle.get("status") == "INVALID_INPUT": return bundle
    context = _bounded_object(context_raw) if context_raw else None
    if context_raw and (not isinstance(context, dict) or context.get("status") == "INVALID_INPUT"): return context
    result = verify_bundle(bundle, context)
    result.update({"authority_effect":"NONE","execution_effect":"NONE","registration_effect":"NONE"})
    return result
def register_foundation(mcp:Any,*,include_institution=False)->Any:
    @mcp.tool(annotations=READ_ONLY)
    def foundation_status():return {"name":"seedpea-foundation","version":FOUNDATION_VERSION,"effects":{"authority":"NONE","execution":"NONE","registration":"NONE"},"profile":"minimal"}
    @mcp.tool(annotations=READ_ONLY)
    def review_evaluator_grant_json(grant_json:str):return _review(grant_json, review_evaluator_grant)
    @mcp.tool(annotations=READ_ONLY)
    def review_release_envelope_json(release_json:str):return _review(release_json, review_release_envelope)
    @mcp.tool(annotations=READ_ONLY)
    def inspect_authority_separation_json(crossing_json:str):return _review(crossing_json, inspect_authority_separation)
    @mcp.tool(annotations=READ_ONLY)
    def pal_review_packet(packet_json:str):return _review(packet_json, review_pal_packet)
    @mcp.tool(annotations=READ_ONLY)
    def pal24_review_resume(packet_json:str):
        """Compare declared recovered work and distinct current conditions; no authority or general continuation proof."""
        return _review(packet_json, review_pal24_resume)
    @mcp.tool(annotations=READ_ONLY)
    def pal24_review_resources(packet_json:str):
        """Review finite nested resource attribution; an unknown required cost stays unknown."""
        return _review(packet_json, review_pal24_resources)
    @mcp.tool(annotations=READ_ONLY)
    def pal24_source_profile_resource():return pal24_source_profile()
    @mcp.tool(annotations=READ_ONLY)
    def charter_check_contract(contract_json:str):return _review(contract_json, check_charter_contract)
    @mcp.tool(annotations=READ_ONLY)
    def pecan_check_crossing(crossing_json:str,observed_at:str|None=None):return _review(crossing_json, lambda value: check_pecan_crossing(value,observed_at))
    @mcp.tool(annotations=READ_ONLY)
    def pea_explain_candidate(candidate_json:str):return _review(candidate_json, explain_pea_candidate)
    @mcp.tool(annotations=READ_ONLY)
    def seed_review_release(release_json:str):return _review(release_json, review_seed_release)
    @mcp.tool(annotations=READ_ONLY)
    def source_registry_resource(query_json:str=""):
        return source_registry() if not query_json else _review(query_json, source_registry)
    @mcp.tool(annotations=READ_ONLY)
    def compatibility_profile_resource(pal_version:str="2.4"):return compatibility_profile(pal_version)
    @mcp.tool(annotations=READ_ONLY)
    def peaches_prepare_stamp(payload_json:str, context_json:str=""):return _peaches_prepare(payload_json,context_json)
    @mcp.tool(annotations=READ_ONLY)
    def peaches_verify_stamp(bundle_json:str, context_json:str=""):return _peaches_verify(bundle_json,context_json)
    if include_institution:
        @mcp.tool(annotations=READ_ONLY)
        def review_institutional_branch_registration_json(registration_json:str):return _review(registration_json, review_institutional_branch_registration)
    return mcp
