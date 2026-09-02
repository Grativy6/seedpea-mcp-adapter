# Changelog

All notable changes to this adapter are recorded here. Adapter versions are
separate from PAL, PECAN, PEA Core, SEED, and SeedPEA document versions.

## 0.1.0 - Public preview

- Replaced the June keyword classifier with deterministic declaration checks.
- Added evaluator-grant, release-envelope, and authority-separation reviews.
- Added a non-executing institutional branch-registration declaration review.
- Added explicit `authority_effect: NONE` and `execution_effect: NONE` results.
- Added a versioned status resource and controlling-source manifest.
- Added tests for missing fields, version mismatch, collapsed authority roles,
  and non-executing status.
- Rejected duplicate JSON keys, non-finite numbers, and oversized numeric
  literals at the input boundary.
- Documented institutional, data, migration, and non-conformance boundaries.

## June 2026 prototype

- Added a local FastMCP server, echo tool, and placeholder keyword classifier.
- Kept the repository private pending boundary review.
