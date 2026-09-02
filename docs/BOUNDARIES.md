# SeedPEA Adapter Boundaries

## Public route

The intended institutional route is:

1. PAL v2.2 or another sufficiently traceable carrier supplies scoped
   structural evidence.
2. PECAN v1.0.4 detects and routes a consequential crossing.
3. PEA Core v1.1.3 performs a bounded candidate review under an externally
   issued evaluator grant.
4. An accountable human or institution makes, communicates, contests, and
   carries the decision under its own authority.
5. SEED v0.3 may govern a later human-facing release.

Information may return for correction or reopening. Authority does not flow
backward, and later outcomes do not authorize earlier crossings.

## Institutional branch registration

SeedPEA is intended to provide an institution-facing portal to Branchline
services. A person may hold a personal branch; through SeedPEA, an institution
may instead be the declared holder of an institutional branch.

That change in holder does not erase people or give the branch universal
authority. A proposed registration must keep the institution's identity and
authority source, responsible human roles, authorized operators, purpose,
scope, affected people, consent dependencies, data access, retention, contest,
refusal, correction, remedy, expiry, revocation, lineage, and accountable
boundary explicit. The rights and standing of affected people remain external
constraints on what the institution or branch may do.

The current adapter only reviews whether those declarations are present. It
does not register a branch, verify an institution, create an account, assign a
role, grant access, establish jurisdiction, obtain consent, or authorize use of
any Branchline service. Registration does not transfer ownership, rights,
consent, standing, or authority from a person or community to an institution.

Declaration values remain opaque except that responsible-human roles and
authorized operators must each be supplied as a non-empty list of non-empty
strings. Presence does not verify identity, uniqueness, employment,
appointment, ownership, authority, or the truth of any declaration.

## Adapter role

The adapter checks declared structure. It does not verify that a source is
truthful, that a grant is legitimate, that consent exists, that an institution
has jurisdiction, or that a proposed action is ethical or lawful.

Its status namespace is deliberately small:

- `COMPLETE_FOR_REVIEW`
- `INCOMPLETE`
- `INVALID_INPUT`

These are adapter inspection statuses. They are not PAL closure states, PECAN
routing states, PEA candidate judgments, accountable decisions, execution
states, or SEED release states.

## Data boundary

The current adapter accepts JSON strings supplied directly to a tool call and
returns field-level findings. It does not retain the packet, open files, call a
model, invoke a network service, execute shell commands, or write a decision.
The preview rejects inputs longer than 100,000 characters and does not include
the submitted packet in its findings.

Institutions remain responsible for input minimization, lawful handling,
retention, access control, professional duties, affected-party participation,
contest, remedy, and every consequential decision or action.

## Migration rule

Any later code imported from Branchline, Strongwiz, or another project requires
an explicit source record, compatibility review, versioned migration note, and
fresh tests. Shared lineage or successful execution does not silently promote
experimental code into this public adapter.
