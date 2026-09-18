# SeedPEA MCP Adapter

SeedPEA provides a small, local foundation for systems that need traceable
reasoning, separately sourced grants, candidate review, and room for human
choice. Its default adapter contains PAL, CHARTER, PECAN, PEA, SEED, source and
compatibility checks, and offline PEACHES preparation and verification.

**Review build: adapter 0.2.0; shared foundation 0.1.0.** This is a finite
software adaptation with explicit limits, not blanket framework conformance.
Christopher Daniel Pang authored the source frameworks; AI assistance remains
tool assistance.

## Install and connect

Python 3.11 or later is required. The three required distributions are
`peaches-book==0.1.0`, `seedpea-foundation==0.1.0`, and
`seedpea-mcp-adapter==0.2.0`. Review artifacts are not published to a package
registry. Install their wheels from the build wheelhouse, or install the Book
of Peaches checkout, this repository's foundation, and this checkout in order:

```text
python -m pip install <book-of-peaches-checkout>
python -m pip install ./packages/foundation
python -m pip install .
python -m seedpea_adapter.server
```

The last command starts an MCP stdio server. Configure the host with the virtual
environment's Python executable and arguments `["-m","seedpea_adapter.server"]`.
No model, running Hearthline service, private repository, scheduler, signing
key or production book is required.

## Supported operations

| Tool | Finite operation |
| --- | --- |
| `pal_review_packet` | Account snapshots, immutable receipt continuity, separate tests and scoped closure, residuals and reopening. |
| `charter_check_contract` | Separate work, completion-criterion and ledger duties; finite limits, selected carry and finish evidence. |
| `pecan_check_crossing` | Separate stages and declared subject/object/action/scope, consent, expiry, revocation and remaining uses. |
| `pea_explain_candidate` | Scoped evaluator grant, sourced reasons and unresolved conditions for human review. |
| `seed_review_release` | Sourced claims, limits, choices, refusal, correction, reopening and natural stop. |
| `source_registry_resource` | List/search references, exact-version read, compare supplied content to a declared digest. |
| `compatibility_profile_resource` | PAL 2.3 adaptation, original PAL 2.2 preview and unchanged PPP 0.6 declaration. |
| `peaches_prepare_stamp`, `peaches_verify_stamp` | Prepare test input or verify signatures under separately supplied context. No append. |

The three minimal preview checks remain available through the same maintained
implementation. Set `SEEDPEA_PROFILE=institution` to include the optional
institutional declaration check. It does not create accounts or submit to an
institution. The shared foundation is maintained here and used directly by the
public Hearthline toolkit.

JSON arguments are bounded strings. Duplicate keys, malformed values and
excessive inputs are rejected. See [operational contracts](docs/OPERATIONAL_CONTRACTS.md)
for fixtures, statuses and recovery limits.

## Meaning and limits

`STRUCTURALLY_VALID_FOR_NAMED_PROFILE` concerns only the declared finite
profile. It supplies no truth, ethics, consent, standing, permission or
authority. PECAN reports declared current grant usability separately from
structural validity. PEA leaves disposition to the human route. PEACHES
verification cannot manufacture a canonical registration receipt.

No reviewed action is executed; grants are not consumed or renewed. No model
call, private-memory access or recurring work is performed.

The source versions remain PAL 2.3, CHARTER 1.0, PECAN 1.0.4, PEA Core 1.1.3,
SEED 0.3 and PPP 0.6. PPP's PAL 2.2 dependency and the original preview's PAL
2.2 target remain historical facts. Native transport profiles and mathematical
realizations are not certified by this adapter. Source references neither
become instructions nor relicense papers.

## Verify and recover

```text
python -m pytest -q tests packages/foundation/tests
```

Cross-adapter integration tests additionally require the separately installed
Hearthline toolkit. The minimal foundation remains usable without it.
The original 16 deterministic preview checks and repository history are retained.

See [boundaries](docs/BOUNDARIES.md), [privacy](docs/PRIVACY.md),
[migration history](docs/MIGRATION.md) and [licensing](LICENSES.md).
