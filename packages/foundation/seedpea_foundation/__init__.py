"""Small deterministic SeedPEA foundation contracts."""
from .contracts import *
from .mcp_tools import register_foundation
from .legacy import (
    ADAPTER_VERSION, MAX_INPUT_CHARS, CONTROLLING_SOURCES,
    GRANT_FIELDS, RELEASE_FIELDS, AUTHORITY_FIELDS,
    INSTITUTIONAL_REGISTRATION_FIELDS, review_json,
    review_evaluator_grant, review_release_envelope,
    inspect_authority_separation, review_institutional_branch_registration,
    status_manifest,
)
