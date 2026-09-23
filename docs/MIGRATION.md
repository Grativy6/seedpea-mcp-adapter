# Public Preview Migration Record

## Source state

The public preview descends from the private June 20, 2026 prototype whose main
head was `feb2d83650a5f6ed924111ead8f1fcc27955ff14`.

That prototype contained a local FastMCP server, an echo tool, a keyword-based
help classifier, a broad environment freeze, and no tests. The public preview
retains the local, text-only, read-only intent while replacing the ungrounded
classifier with deterministic declaration checks.

## Canon migration

The preview declares PAL v2.2, PECAN v1.0.4, PEA Core v1.1.3, and SEED v0.3 as
the versions reviewed for its public boundary. SEED v0.3's original corpus note
references earlier PAL and PEA versions; this adapter's later version manifest
is an explicit implementation migration, not a silent amendment of SEED.

## Exclusions

No live or unpublished Strongwiz state is included. No Branchline user data,
private framework layers, weights, thresholds, keys, routing internals, or
private development notes are included.

Any later adoption from another project requires a new source record,
compatibility review, migration entry, and tests.

## PAL v2.4 finite integration, 2026-09-22

Foundation 0.2.0 and adapter 0.3.0 add separate pointwise recovery and nested
resource profiles. The active registry references PAL v2.4 at DOI
10.5281/zenodo.22888036, with five exact artifact pins in the packaged manifest.
The PAL 2.3 account checker and exact-version registry entry remain unchanged
in meaning; `compatibility_profile_resource(pal_version="2.3")` returns the
historical mapping. The default mapping now describes the additive v2.4 path.
The original preview's PAL 2.2 identity and PPP 0.6 dependency remain historical.

There is no stored-account migration or retroactive relabeling of receipts.
O63-O65 remain OPEN in the source. Tests cover this finite implementation only.
Installations require an explicit package update; repository changes do not
activate a running host or renew any grant. See [the profile](PAL24_PROFILE.md).
