<!--
  Appended by the vtex-cx-engineering preset on top of the core plan template.
  The sections above come from Spec Kit core; the sections below are the VTEX CX
  Golden Path additions. Do not duplicate what the Engineering Spec already
  states — reference it and plan the execution of it.
-->

## Inherited Context

<!--
  Carried over from the Engineering Spec so the plan is traceable on its own.
  These values MUST match spec.md exactly; if they drifted, the spec is the
  source and the plan is wrong. When the spec has no Product Spec, write
  `Product Spec: none` and drop the Pinned version and Architecture doc lines.
-->

- Product Spec: [title — URL | none]
- Pinned version: [commit/tag]
- Architecture doc: [none | URL + commit/tag]
- Engineering Spec: [path to spec.md]

## Delivery Sequence

<!--
  The order of execution, not a restatement of the technical approach. Call out
  what must land before what, and anything that must be coordinated with
  another repository (implementing the same Product Spec, when there is one).
-->

1. [step] — [why it must come at this point]

**Cross-repository coordination**: [what another repo must ship first, or none]

## Peak Load Plan

<!--
  The Engineering Spec declares the expected peak. Here state how the plan
  meets it and how that is verified before the feature is considered done.
-->

- Declared peak: [value from spec.md]
- How this plan sustains it: [capacity decisions, statelessness, external state]
- How it is verified: [load test, staged rollout measurement, or the check used]

## Observability Plan

<!--
  Required so an incident is diagnosable without reproducing it.
-->

- Structured logs added: [where, with which context fields]
- Correlation identifier: [how it enters and how it is propagated]
- Error reports: [which opaque identifiers accompany a reported error]
- Signals watched after rollout: [what tells the team this feature is healthy]

## Rollout and Rollback Plan

- Rollout: [staged enablement, flag, or direct deploy, and in which order]
- Backward compatibility window: [how the previous deployed version keeps working]
- Rollback: [the exact step to undo this, and what makes it safe]
- Migration reversibility: [whether schema changes survive a rollback]

## Divergence Gate

<!--
  A technical need that contradicts something inherited is a divergence and
  MUST NOT be planned into implementation. Raise an amendment in the product
  repository first, record it in the spec's Divergences field, and update the
  pinned version once the amendment is tagged. Remove this section when the
  spec has no Product Spec: nothing is inherited.
-->

- Divergences found while planning: [none | the amendment raised and its link]
- Tasks blocked by an open amendment: [none | which ones, so the rest can proceed]
