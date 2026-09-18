# Operational contract guide

This build checks bounded declared inputs. Host enforcement and external-source
authentication remain separate. It does not issue execution approval.

## Inputs, examples and statuses

Framework tools take named JSON strings. Duplicate keys, malformed syntax,
excessive size/depth and unsupported values are rejected. Typed checks report
`INVALID_INPUT` or `STRUCTURALLY_VALID_FOR_NAMED_PROFILE`; unsupported
PAL payloads carry an explicit unsupported-profile status. Legacy preview
tools retain their field-presence status and its narrower meaning.

Executable positive fixtures and negative mutations define the finite shapes:
[foundation fixtures](../tests/test_operational_contracts.py),
[PAL fixtures](../packages/foundation/tests/test_pal_profile.py), and
[separate-process equivalence](../tests/test_real_adapter_equivalence.py).

PAL binds an operation, account and ordered receipt history. Opening requires
an origin cut. APPEND preserves a prefix; VERSION preserves identity/origin
with a typed delta; legacy migration uses a successor when native continuity
is unavailable. TestReceipts preserve positive and negative evidence. A
ClosureReceipt needs its own envelope and prior evidence; reviews, heartbeats
and stamps cannot supply closure.

CHARTER binds three duties, available and selected carry, finite limits, return
route and finish evidence. It does not select, dispatch, retain data or classify
Systemic Friction.

PECAN binds four separate declaration stages, requested subject/object/action/
scope, grant reference, consent source, accountable boundary and aware time.
Current-usability results include `MATCHES_DECLARED_GRANT_PARAMETERS`,
`OUT_OF_SCOPE`, `EXPIRED`, `REVOKED`, `EXHAUSTED` and unresolved
review. Unknown previous dispatch requires reconciliation. Retries do not
renew a grant. Source declarations are not independently authenticated.

PEA binds an external evaluator grant to this candidate and purpose. Its
explanation carries supplied sourced reasons and preserves disputed conditions.
SEED checks explicit release claims, limits, choice, refusal, correction,
reopening and a natural stop. Neither supplies the human disposition or
certifies human interests.

## Sources and compatibility

Registry operations are `list`, `search`, `read` with exact
`source_id`/`version`, and `verify_content` against
`expected_sha256` for supplied UTF-8 content. Matching a caller-declared hash
does not authenticate a publisher. Content remains reference data, not
instructions. Full papers are not bundled or automatically loaded.

The compatibility resource records source roles, target profiles, mapping
classes and residuals. Original publications remain unchanged. Additional
native obligations reopen through versioned mappings and dedicated fixtures.

## PEACHES and recovery

Preparation is test-only. Verification separates unanchored signatures from
validity under declared context. The Book of Peaches package owns checker
append, inclusion, SQLite recovery, mirrors, export/import and transitions.
Historic receipt validity does not establish current grant usability.
Production identity, custody, governance and real Genesis remain human choices.
