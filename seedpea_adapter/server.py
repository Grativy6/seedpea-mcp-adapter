"""FastMCP transport surface for the SeedPEA public preview."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .core import (
    inspect_authority_separation,
    review_json,
    review_evaluator_grant,
    review_institutional_branch_registration,
    review_release_envelope,
    status_manifest,
)


mcp = FastMCP("seedpea-mcp-adapter")


@mcp.tool()
def review_evaluator_grant_json(grant_json: str) -> dict[str, Any]:
    """Inspect declared PEA evaluator-grant fields without granting authority."""

    return review_json(grant_json, review_evaluator_grant)


@mcp.tool()
def review_release_envelope_json(release_json: str) -> dict[str, Any]:
    """Inspect declared SEED-aligned release fields without approving release."""

    return review_json(release_json, review_release_envelope)


@mcp.tool()
def inspect_authority_separation_json(crossing_json: str) -> dict[str, Any]:
    """Inspect whether crossing roles are separately declared without authorizing action."""

    return review_json(crossing_json, inspect_authority_separation)


@mcp.tool()
def review_institutional_branch_registration_json(
    registration_json: str,
) -> dict[str, Any]:
    """Inspect an institutional branch declaration without registering it."""

    return review_json(registration_json, review_institutional_branch_registration)


@mcp.resource("seedpea://status")
def status() -> str:
    """Return the adapter's versioned status and non-claims."""

    return json.dumps(status_manifest(), indent=2, sort_keys=True)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
