"""FastMCP transport surface for the SeedPEA public preview."""

from __future__ import annotations

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .core import status_manifest
from seedpea_foundation.mcp_tools import register_foundation
from seedpea_foundation.contracts import compatibility_profile


mcp = FastMCP("seedpea-mcp-adapter")
profile = os.environ.get("SEEDPEA_PROFILE", "minimal")
if profile not in ("minimal", "institution"):
    raise ValueError("SEEDPEA_PROFILE must be minimal or institution")
register_foundation(mcp, include_institution=profile == "institution")


@mcp.resource("seedpea://status")
def status() -> str:
    """Return the adapter's versioned status and non-claims."""

    return json.dumps({"adapter_version":"0.3.0", "foundation_version":"0.2.0",
                       "profile":profile, "integration":compatibility_profile(),
                       "preserved_legacy_preview":status_manifest()}, indent=2, sort_keys=True)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
