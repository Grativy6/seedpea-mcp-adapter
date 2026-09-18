"""Public SeedPEA MCP adapter and shared foundation entry point."""
from seedpea_foundation import FOUNDATION_VERSION, register_foundation

from .core import (
    ADAPTER_VERSION,
    inspect_authority_separation,
    review_evaluator_grant,
    review_institutional_branch_registration,
    review_release_envelope,
    status_manifest,
)

__all__ = [
    "ADAPTER_VERSION",
    "inspect_authority_separation",
    "review_evaluator_grant",
    "review_institutional_branch_registration",
    "review_release_envelope",
    "status_manifest",
]
