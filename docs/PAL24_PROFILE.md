# PAL 2.4 finite continuation and resource profile

`seedpea_foundation.pal24` is an additive, read-only adapter profile for a
small portion of PAL v2.4. It preserves the PAL 2.3 profile and does not
claim blanket PAL conformance. The published source remains the authority for
the full contract: [PAL v2.4](https://zenodo.org/records/22888036).

## Continuation review

`review_pal24_resume(packet)` accepts a bounded JSON-like packet:

```json
{
  "operation": "RESUME",
  "checkpoint": {
    "checkpoint_id": "cp-1",
    "work_state": {"cursor": 4},
    "task_version": "task-1",
    "task_id": "task-1", "projection_id": "projection-1",
    "transition_ref": "transition-1", "observation_ref": "observation-1",
    "horizon": "POINTWISE",
    "admitted_suffix": ["event-1"],
    "source_bindings": [{
      "source_id": "source-a", "version": "1",
      "expected_hash": "sha256:9dd77bd655a37c1c9497f943771ccd857345873a80ae6023d7157ad3dab23742"
    }],
    "requirements": [{"requirement_id": "r1", "field": "mode",
      "equals": "safe", "evidence_refs": ["ev1"]}]
  },
  "observed": {"work_state": {"cursor": 4}, "task_version": "task-1",
    "task_id": "task-1", "projection_id": "projection-1",
    "transition_ref": "transition-1", "observation_ref": "observation-1",
    "horizon": "POINTWISE", "admitted_suffix": ["event-1"],
    "source_bindings": [{"source_id": "source-a", "version": "1",
      "expected_hash": "sha256:9dd77bd655a37c1c9497f943771ccd857345873a80ae6023d7157ad3dab23742",
      "content": "exact source bytes"}],
    "requirements": [{"requirement_id": "r1", "field": "mode",
      "equals": "safe", "evidence_refs": ["ev1"]}]},
  "current": {"facts": {"mode": {"value": "safe",
    "evidence_refs": ["ev1"]}}, "grant": {"status": "ACTIVE"},
               "resources": {"status": "AVAILABLE"}}
}
```

The checker reports exact protected-work recovery separately from task
version, admitted suffix, source identity, current applicability, current
grant, and current resource state. A matching work digest does not establish
answer equality or continuation equivalence. Those claims remain
`NOT_ASSESSED` unless a future bounded profile supplies an explicit transition
and observation contract. `UNKNOWN`, expired, revoked, or exhausted states
remain unresolved and do not become a pass or a zero cost.

The checkpoint's requirements are inherited and mandatory. An explicitly empty
list means that no conditions were declared; omission is invalid. Each
requirement is evaluated against `current.facts`, including its evidence
references, with exact typed comparison (`true` is not integer `1`). If the
observed record changes the list, this review is unresolved even when a
successor record is supplied: creating a successor checkpoint is a separate
operation. Source identity is compared by ID and version, while source
content is hashed as canonical JSON (UTF-8, sorted keys, compact separators, no NaN)
against the frozen checkpoint digest. This differs from the raw DOCX file hashes
in the source manifest. Claimed hashes
without content remain `UNKNOWN`.

## Nested resource review

`review_pal24_resources(packet)` checks a finite acyclic tree. Every node
declares the same unit, epoch, and boundary. Event IDs are unique across the
tree and each event has one owning node. A parent-exclusive event is counted
once at its declared parent. A complete node must include
`expected_child_ids`; missing in-scope children are an error. `complete` must
be explicit. An `UNKNOWN` amount remains unknown, so a subtotal cannot
establish a complete total; the returned `accounting.total` is `null` until
the tree is complete and all costs are known. Reset and top-up mutation fields
are outside this profile and rejected.

Both functions are pure checks. They do not replay code, authenticate a
caller, create authority, renew a grant, execute an action, or register a
stamp. Inputs are bounded to 100,000 UTF-8 bytes, depth 24, and 10,000 JSON
nodes; floats, non-string mapping keys, and unsupported values are rejected.
