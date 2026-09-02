# SeedPEA MCP Adapter

SeedPEA is Branchline Systems' institution-facing portal. It is intended to
let an institution register and steward a Branchline branch in its own name,
rather than attaching every branch directly to an individual person. This
repository is an early, local MCP implementation surface for that direction.

Institutional registration does not make an institution anonymous or
self-authorizing. A declared branch boundary must still keep responsible human
roles, authorized operators, the institution's authority source, scope,
affected people, consent dependencies, contest, expiry, and revocation visible.
Refusal, correction, and remedy routes must remain visible as well.

**Status:** public preview (`0.1.0`), experimental, non-self-executing, and not
a specification-conformance claim.

Christopher Daniel Pang is the author and original steward of the associated
framework lineage. AI systems assist as tools; they are not co-authors or
authorities.

## What this adapter does

The adapter performs deterministic structural checks on user-supplied JSON:

- `review_evaluator_grant_json` checks whether the declared PEA evaluator-grant
  boundary is complete enough to be returned for accountable review.
- `review_release_envelope_json` checks whether a human-facing release declares
  minimum public boundary fields such as audience, purpose, uncertainty,
  privacy, correction, contest, stopping, and reopening.
- `inspect_authority_separation_json` checks that description, recommendation,
  permission, and authorization remain separately declared.
- `review_institutional_branch_registration_json` checks whether a proposed
  institution-held branch declares the minimum registration boundary for later
  accountable review.
- `seedpea://status` reports the adapter version, reviewed source versions,
  effects, and non-claims.

`COMPLETE_FOR_REVIEW` means only that the required fields are present and
non-blank. It does **not** mean true, safe, ethical, compliant, permitted,
authorized, approved, or ready to execute.

For an institutional branch declaration, responsible-human roles and
authorized operators must also be non-empty lists of non-empty strings. The
adapter does not verify the identities, relationships, or authority claimed by
those strings.

## Current boundary

- Local MCP transport
- Text/JSON inputs and outputs
- Deterministic, read-only inspection
- No model call
- No filesystem access
- No shell execution
- No credential access
- No network or external API access
- No autonomous decision or action
- No branch, account, role, or operator registration
- A 100,000-character input ceiling for this preview

The adapter does not make law, certify compliance, determine institutional
policy, manufacture consent or standing, authorize execution, or replace
affected people, professional duties, democratic processes, or accountable
judgment.

The SeedPEA portal itself is not implemented in this preview. The registration
tool checks a declaration only; it does not create a branch, account,
institutional relationship, user role, permission, or authorization.

## Install and run

Python 3.11 or newer is required.

```bash
python -m venv .venv
python -m pip install -e .
python server.py
```

Run the deterministic core tests without starting the MCP server:

```bash
python -m unittest discover -s tests -v
```

## Source boundaries

This adapter is informed by the following public sources, each controlling only
its declared role:

- [PAL v2.2](https://doi.org/10.5281/zenodo.21891598) — structural trace,
  authority ceilings, residuals, and reopening.
- [PECAN v1.0.4](https://doi.org/10.5281/zenodo.21760884) — consequential
  crossings and authority lineage.
- [PEA Core v1.1.3](https://doi.org/10.5281/zenodo.21911684) — bounded authority
  audit and candidate ethical review under an external grant.
- [SEED v0.3](https://doi.org/10.5281/zenodo.21760893) — human-facing release
  discipline preserving agency and room to stop.

These materials belong to one authored lineage and are not independent
corroboration of one another. This implementation does not claim conformance to
any of them.

## Development lineage

The June 2026 prototype used a keyword classifier and an echo tool. The public
preview removes both because keyword matching cannot honestly establish a help,
ethical, permission, or authority boundary. Later implementations may extend
the typed review surface through explicit versioned migrations and tests.

Strongwiz and the Branchline application are separate projects. No live or
unreleased Strongwiz working state is included here.

See [Boundaries](docs/BOUNDARIES.md), [Privacy](docs/PRIVACY.md),
[Migration](docs/MIGRATION.md), [Changelog](CHANGELOG.md), and
[Licensing](LICENSES.md).
