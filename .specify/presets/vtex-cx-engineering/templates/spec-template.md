# Engineering Specification: [FEATURE NAME]

**Repository**: [repository name] — [backend | frontend | frontend-platform | cloud]

**Feature Branch**: `[###-feature-name]`

**Created**: [DATE]

**Status**: Draft

<!--
  This is an ENGINEERING spec. It answers HOW this repository implements a
  change.

  With a Product Spec, it MUST NOT restate the what: problem, scope rationale,
  success criteria, user stories and binding decisions are inherited and are
  not repeated here. A need that contradicts anything inherited is a
  divergence, not a decision — see the Divergences section.

  Without a Product Spec, the what is limited to the problem and acceptance
  criteria of the origin section.

  Remove any section that genuinely does not apply. Do not leave it as "N/A".
-->

## Inheritance from Product Spec

<!--
  Required by the root constitution, in exactly this format. The pinned
  version MUST be an immutable commit or tag; a mutable URL or ID alone is not
  acceptable. The architecture doc is optional and only exists when the feature
  went through the architecture stage. Use this block only when the change has
  a Product Spec; otherwise use the origin block below.
-->

- Product Spec: [title] — [URL]
- Pinned version: [commit/tag]
- Architecture doc: [none | URL + commit/tag]
- Inherited binding decisions: [short list]
- Scope of this spec: [slice implemented by this repo]
- Divergences: [none | link to amendment]

## Origin Without Product Spec

<!--
  Use this block instead of the inheritance block when the change has no
  Product Spec (a hotfix, a fix, technical debt). Keep exactly one of the two
  and delete the other. Required by the root constitution, in exactly this
  format.
-->

- Product Spec: none
- Problem: [what is wrong or missing, in one or two sentences]
- Acceptance criteria: [observable outcomes that prove the change is done]

## Scope in This Repository

<!--
  The boundary of this spec inside this service. Frontend and backend write
  separate specs (from the same Product Spec, when there is one), so state
  what this repo owns and what it expects another repo to deliver.
-->

**This repository implements**: [capabilities delivered here]

**Out of scope here**: [slices owned by other repositories or deferred, and who owns them]

**Depends on**: [other repos, services or teams this slice needs, and the contract it needs from them]

## Current State

<!--
  What already exists in this codebase that the feature touches: modules,
  endpoints, models, jobs, components. Anchor the plan in reality instead of
  describing a greenfield.
-->

- [existing component or module] — [what it does today and how this feature changes it]

## Technical Approach

<!--
  The core of the spec: how this service delivers its slice. Describe the
  components involved and the flow through them, in the direction the
  repository constitution mandates for layering.
-->

### Components Affected

| Component | Change | Why |
|-----------|--------|-----|
| [path or module] | [new / modified / removed] | [reason] |

### Flow

[Describe the end-to-end path through this service for the main case: entry point, validation boundary, business logic, outbound calls, persisted effect.]

### Rejected Alternatives

- [alternative]: [why it was rejected]

## Contracts

<!--
  Any public interface this feature adds or changes — HTTP endpoints, events
  published or consumed, task signatures, exported components or types. The
  root constitution requires SemVer versioning and either backward
  compatibility or an announced deprecation path. Silent breaking changes are
  forbidden.
-->

| Interface | Change | Version impact | Backward compatible |
|-----------|--------|----------------|---------------------|
| [name] | [added / modified / deprecated] | [major / minor / patch] | [yes / no + deprecation path] |

**Consumers affected**: [who depends on these contracts and how they are notified]

## Data Model and Migrations

<!--
  Entities and persisted state introduced or changed. Migrations must be
  backward compatible with the previously deployed version so a rollout can be
  rolled back. Remove this section when the feature persists nothing.
-->

- **[Entity]**: [fields that matter, relationships, ownership]

**Migrations**: [schema changes, backfill strategy, and whether the previous deployed version still works against the new schema]

## Non-Functional Requirements

### Peak Load

<!--
  Stated as peak, not average — required by the backend constitution. Include
  the window it refers to (for example a seasonal sales peak).
-->

[expected peak, with unit and window]

### Observability

[What is logged and with which context; which correlation identifier is propagated; which metrics or traces make this feature diagnosable. Logs must be structured and must never carry secrets or sensitive personal data.]

### Failure Handling

[How each external dependency can fail, the explicit timeout used, what the caller sees on failure, and the retry policy where data is propagated to another service: which failures are retriable, max attempts, backoff, and what keeps the operation idempotent.]

### Security and Authorization

[Which inputs cross the trust boundary and where they are validated; which authorization check is enforced server-side; which secrets are needed and how they are injected at runtime.]

## Test Strategy

<!--
  With a Product Spec, acceptance is measured against its inherited success
  criteria: do not restate them here — map them to the tests that prove them
  in this repository. Without a Product Spec, map the acceptance criteria of
  the origin section; for a fix, include the test that reproduces the bug.
-->

| Success / acceptance criterion | How this repository proves it |
|--------------------------------|-------------------------------|
| [inherited success criterion, or acceptance criterion from the origin section] | [the flow test or check that covers it] |

**Flow coverage**: [the complete use cases covered end to end, from input to resulting effect]

**Failure paths covered**: [the error paths exercised by tests]

**Stubbed at the boundary**: [which external dependencies are stubbed, and at which seam]

## Rollout and Rollback

[Deployment order across repositories if it matters, any feature flag or staged enablement, how the change is rolled back, and what makes the previous version still viable after rollback.]

## Constitution Alignment

<!--
  Checked against .specify/memory/constitution.md. Every MUST that this feature
  touches gets a row. A departure must be justified here, in the spec — never
  in the code.
-->

| Principle | How this spec complies | Exception + justification |
|-----------|------------------------|---------------------------|
| [principle name] | [how] | [none, or the justified departure] |

## Implementation Decisions

<!--
  Technical decisions that contradict nothing inherited. These belong here and
  are not divergences.
-->

- **[decision]**: [what was chosen and the constraint or trade-off behind it]

## Divergences

<!--
  Only for a technical need that contradicts something inherited: scope, a
  success criterion, or a binding decision. The divergence MUST NOT be
  implemented. Raise an amendment in the product repository, link it here, and
  update the Pinned version once the amendment produces a new tag. Remove this
  section when there is no Product Spec: nothing is inherited.
-->

[none]

## Open Questions

<!--
  Maximum 3 markers. Anything blocking the plan should be resolved before
  moving on.
-->

- [NEEDS CLARIFICATION: specific question]
