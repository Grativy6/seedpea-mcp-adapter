# SeedPEA foundation

`seedpea-foundation` is the independently installable minimal floor used by
SeedPEA and intended for reuse by the public Hearthline adapter. It contains
deterministic, bounded structural checks for PAL, CHARTER, PECAN, PEA and
SEED, plus a declared source and compatibility profile.

The package does not make general harmfulness judgments, grant authority,
execute actions, create stamps, or claim conformance to a source
specification. Every result carries `authority_effect: NONE` and
`execution_effect: NONE`.

Install `seedpea-foundation==0.1.0` as its own distribution, then install the
adapter `seedpea-mcp-adapter==0.2.0`. The adapter depends on the foundation and
reexports its legacy preview surface; the foundation can be installed and
used independently by another adapter. The shared MCP registration function
is:

```python
from seedpea_foundation.mcp_tools import register_foundation
register_foundation(mcp, include_institution=False)
```

The institutional profile is opt-in. No private repository, model provider,
scheduler, lore, or live book key is required.

PAL 2.3 and PPP 0.6 appear as an explicit compatibility profile. Version
labels are mappings and do not establish formal conformance.
