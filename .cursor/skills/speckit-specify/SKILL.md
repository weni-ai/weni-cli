---
name: speckit-specify
description: Create or update the Engineering Spec of this repository, inherited from
  a pinned Product Spec or originated in engineering, and bound by the repository
  constitution.
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: preset:vtex-cx-engineering
---

# Speckit Specify Skill

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## What This Command Produces

An **Engineering Spec**: how *this repository* implements a change. It is not a product spec and not a plan. It has one of two origins, and both are regular paths of the process:

- **With a Product Spec** — the change is the slice this repository owns of a feature already specified by product. The **what** — problem, scope rationale, success criteria, user journeys, binding decisions — is **inherited** from the Product Spec and MUST NOT be restated or redefined here.
- **Without a Product Spec** — the change originates in engineering (a hotfix, a fix, technical debt). There is nothing to inherit, so the spec states its own **what**, briefly: the problem and the acceptance criteria. No justification for the absence is needed.

Either origin may follow the full cycle (plan, tasks, analyze, implement) or the lite cycle (implement directly). The cycle is chosen by complexity, not by origin.

- The **how** in this service — components, contracts, data, peak load, observability, failure handling, tests, rollout — **is** the body of this document.
- Technical detail is **required**, not avoided. This document is written for the engineers of this repository.
- A technical need that contradicts something inherited is a **divergence**: it MUST NOT be implemented or quietly absorbed into the spec. See the Divergence Rule below.

## Pre-Execution Checks

**Check for extension hooks (before specification)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_specify` key
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that `.specify/extensions.yml` could not be read (include the parser error) and that no hooks were checked, including any mandatory (`optional: false`) hooks registered there, then continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `/speckit-git-commit`.
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Gate 0 — Origin (blocking)

**Run this before creating any directory or file.** The origin decides how the spec opens: an inheritance section pinned to a Product Spec, or an origin section of its own.

1. **Ask for the origin.** The developer keeps the product specs repository cloned locally and points at the file directly. If the user input already gives the path to a Product Spec, or already states that there is no Product Spec, use that and do not ask again. Otherwise ask:

   > Does this change derive from a Product Spec? If it does, give me the path to the spec file in your local clone of the product specs repository, and the path to the architecture document if the feature went through the architecture stage. If it does not, just say there is no Product Spec.

   **STOP and wait for the answer.** Do not decide on your own that there is no Product Spec, do not guess a path, do not search the product repository for a plausible spec, and do not proceed with a placeholder.

   - **No Product Spec**: this is a regular path and needs no justification. Skip items 2 to 5 and go to Gate 1. The spec will open with `## Origin Without Product Spec`.
   - **A path was given**: continue with items 2 to 5.

2. **Resolve the immutable reference.** For the product spec file, and again for the architecture document when one was given, run (substituting the file's directory and path):

   ```
   git -C "<spec-dir>" rev-parse --show-toplevel
   git -C "<spec-dir>" remote get-url origin
   git -C "<spec-dir>" rev-parse HEAD
   git -C "<spec-dir>" describe --tags --exact-match HEAD
   git -C "<spec-dir>" status --porcelain -- "<spec-file>"
   ```

   - Prefer the **exact tag** as the pinned version. If `describe --exact-match` fails, use the full HEAD commit SHA and tell the user the spec is pinned to a commit rather than a tag.
   - Build the permanent URL from the remote and the resolved commit, for example `https://github.com/<owner>/<repo>/blob/<commit>/<path-within-repo>`. Normalize an SSH remote (`git@github.com:owner/repo.git`) to its HTTPS form and strip the trailing `.git`.

3. **Refuse to pin a moving target.** Stop and report, rather than writing the spec, when any of these hold:

   - The path does not exist, or is not inside a git repository.
   - `status --porcelain` shows the file as modified or untracked — the content you are about to read is not the content the pinned version points at.
   - The local clone is behind and the user has not confirmed which version is authoritative.

   Say exactly what is wrong and what would unblock it (commit and tag the product spec, pull the clone, or point at the right file). Do not create `specs/<feature>/` in this state, and do not fall back to the no-Product-Spec path on your own: a Product Spec that exists but is not pinnable is a blocker, not an absence.

4. **Read the inherited documents in full** — the Product Spec, and the architecture document when present. Extract and keep for later:

   - Problem and scope, so you can tell what this repository owns and what it does not.
   - **Success criteria**, verbatim, to be mapped to tests later. They are not rewritten.
   - **Binding decisions** — anything the Product Spec or architecture document already settled that constrains this service.
   - Non-functional requirements that became binding (scale, latency, security).

## Gate 1 — Constitution (binding)

Load `.specify/memory/constitution.md`.

This document is a **binding input to the spec**, not background reading. Treat every `MUST` as a requirement the spec has to satisfy or explicitly justify:

- The opening section format it mandates for this origin — inheritance or origin without Product Spec — is the format you use, character for character.
- Any obligation it places on an engineering spec — a declared peak load, a named observability contract, a test strategy, a migration rule — MUST appear as filled content in the spec, not as a placeholder.
- A departure from a principle MUST be justified in the `Constitution Alignment` section of the spec. It MUST NOT be left for the code to reveal.

If the constitution does not exist, stop and tell the user to run the `setup-engineering` skill first. Do not write an engineering spec without one.

## Outline

The text the user typed after `/speckit-specify` in the triggering message **is** the feature description. Assume you always have it available in this conversation even if `$ARGUMENTS` appears literally below. Do not ask the user to repeat it unless they provided an empty command.

Given that feature description, and only after Gates 0 and 1 have passed, do this:

1. **Generate a concise short name** (2-4 words) for the feature:
   - Analyze the feature description and extract the most meaningful keywords
   - Create a 2-4 word short name that captures the essence of the feature
   - Use action-noun format when possible (e.g., "add-user-auth", "fix-payment-bug")
   - Preserve technical terms and acronyms (OAuth2, API, JWT, etc.)
   - Keep it concise but descriptive enough to understand the feature at a glance

2. **Branch creation** (optional, via hook):

   If a `before_specify` hook ran successfully in the Pre-Execution Checks above, it will have created/switched to a git branch and output JSON containing `BRANCH_NAME` and `FEATURE_NUM`. Note these values for reference, but the branch name does **not** dictate the spec directory name.

   If the user explicitly provided `GIT_BRANCH_NAME`, pass it through to the hook so the branch script uses the exact value as the branch name (bypassing all prefix/suffix generation).

3. **Create the spec feature directory**:

   Specs live under the default `specs/` directory unless the user explicitly provides `SPECIFY_FEATURE_DIRECTORY`.

   **Resolution order for `SPECIFY_FEATURE_DIRECTORY`**:
   1. If the user explicitly provided `SPECIFY_FEATURE_DIRECTORY`, use it as-is
   2. Otherwise, auto-generate it under `specs/`:
      - The prefix is always `NNN`: the next available 3-digit sequential number after scanning existing directories in `specs/` (highest existing number + 1, starting at `001`). Never use a date or timestamp prefix, regardless of `feature_numbering` or `branch_numbering` in `.specify/init-options.json`
      - Construct the directory name: `<prefix>-<short-name>` (e.g., `003-user-auth`)
      - Set `SPECIFY_FEATURE_DIRECTORY` to `specs/<directory-name>`

   **Create the directory and spec file**:
   - `mkdir -p SPECIFY_FEATURE_DIRECTORY`
   - Resolve the active `spec-template` through the Spec Kit preset/template resolution stack (equivalent to `specify preset resolve spec-template`)
   - Copy the resolved `spec-template` file to `SPECIFY_FEATURE_DIRECTORY/spec.md` as the starting point
   - Set `SPEC_FILE` to `SPECIFY_FEATURE_DIRECTORY/spec.md`
   - Persist the resolved path to `.specify/feature.json`:
     ```json
     {
       "feature_directory": "<resolved feature dir>"
     }
     ```
     Write the actual resolved directory path value (for example, `specs/003-user-auth`), not the literal string `SPECIFY_FEATURE_DIRECTORY`.
     This allows downstream commands (`/speckit-plan`, `/speckit-tasks`, etc.) to locate the feature directory without relying on git branch name conventions.

   **IMPORTANT**:
   - You must only create one feature per `/speckit-specify` invocation
   - The spec directory name and the git branch name are independent
   - The spec directory and file are always created by this command, never by the hook

4. Load the resolved active `spec-template` file to understand required sections.

5. **Survey the codebase before writing.** An engineering spec that does not know what already exists is a guess. Inspect this repository for what the feature touches: the modules, endpoints, models, events, jobs or components involved, the layering the constitution mandates, the existing test seams, and the nearest analogous feature already implemented. Name real paths. If the repository has an agent context file (`AGENTS.md`, `CLAUDE.md` or equivalent), read it.

6. Follow this execution flow:

   1. Parse the feature description from the user input.
      If empty: ERROR "No feature description provided"
   2. Fill the opening section and delete the other one from the template:
      - **With a Product Spec**: fill `## Inheritance from Product Spec` from the values resolved in Gate 0. Every field is filled; `Pinned version` is a commit or tag, never a bare URL. `Divergences` starts as `none`.
      - **Without a Product Spec**: fill `## Origin Without Product Spec`. `Product Spec` is `none`; `Problem` states what is wrong or missing in one or two sentences; `Acceptance criteria` lists observable outcomes that prove the change is done. Derive them from the user input and the codebase survey; this is the only place the spec states its own what.
   3. Fill `## Scope in This Repository`: what this repo delivers, what belongs to another repository (implementing the same Product Spec, when there is one), and the contract it needs from them.
   4. Fill `## Current State` from the survey in step 5, with real paths.
   5. Fill `## Technical Approach`: components affected, the flow through this service, and the alternatives you rejected with the reason.
   6. Fill `## Contracts` for every public interface added or changed, with its SemVer impact and whether it is backward compatible or ships a deprecation path.
   7. Fill `## Data Model and Migrations` when the feature persists state, including whether the previously deployed version still works against the new schema.
   8. Fill `## Non-Functional Requirements`: peak load as a peak with its window, the observability contract, failure handling and retry policy, and the trust boundary and authorization checks.
   9. Fill `## Test Strategy` by mapping each criterion to the test in this repository that proves it. With a Product Spec, these are the **inherited** success criteria: do not invent new ones and do not restate them as if they were yours. Without a Product Spec, these are the acceptance criteria of `## Origin Without Product Spec`; for a fix, include the test that reproduces the bug.
   10. Fill `## Rollout and Rollback`.
   11. Fill `## Constitution Alignment` with a row for every principle this feature touches, and an explicit justification for any departure.
   12. Fill `## Implementation Decisions` with the technical decisions that contradict nothing inherited.
   13. Fill `## Divergences` — `none`, or the amendment link if the Divergence Rule below was triggered. Without a Product Spec there is nothing to diverge from: remove the section.
   14. For genuinely unclear aspects, prefer an informed decision recorded in `Implementation Decisions` over a question. Use `[NEEDS CLARIFICATION: specific question]` in `## Open Questions` only when the choice changes the technical approach, there are multiple defensible readings with different consequences, or no reasonable default exists. **LIMIT: maximum 3 markers.**
   15. Return: SUCCESS

7. Write the specification to SPEC_FILE using the template structure, preserving section order and headings, replacing every placeholder with concrete content. Remove a section only when it genuinely does not apply; never leave it as "N/A".

8. **Engineering Spec Quality Validation**: After writing the initial spec, validate it.

   a. **Create the checklist** at `SPECIFY_FEATURE_DIRECTORY/checklists/requirements.md` using the checklist template structure with these items:

      ```markdown
      # Engineering Spec Quality Checklist: [FEATURE NAME]

      **Purpose**: Validate the engineering spec before planning or implementation
      **Created**: [DATE]
      **Feature**: [Link to spec.md]

      ## Inheritance

      - [ ] Exactly one Product Spec is referenced
      - [ ] Pinned version is an immutable commit or tag, not a bare URL or ID
      - [ ] The inheritance section matches the format required by the constitution, field for field
      - [ ] Architecture doc is either `none` or pinned by commit/tag
      - [ ] Inherited binding decisions are listed
      - [ ] The spec does not redefine problem, scope rationale, user journeys or success criteria
      - [ ] Divergences is `none`, or links to an amendment in the product repository

      ## Origin

      - [ ] Product Spec is `none`, and the origin section matches the format required by the constitution, field for field
      - [ ] Problem and acceptance criteria are concrete and observable
      - [ ] Every acceptance criterion maps to a test in this repository

      ## Technical Completeness

      - [ ] Scope in this repository is bounded, and what other repos own is named
      - [ ] Current state references real paths in this codebase
      - [ ] Technical approach names the components affected and the flow between them
      - [ ] Every changed public interface appears in Contracts with its SemVer impact
      - [ ] Backward compatibility or a deprecation path is stated for each breaking change
      - [ ] Data model and migration reversibility are covered, or the feature persists nothing
      - [ ] Peak load is declared as a peak, with its window
      - [ ] Observability states what is logged, with which context, and which correlation identifier
      - [ ] Failure handling states timeouts, retriable failures, bounds and idempotency
      - [ ] The trust boundary and the server-side authorization check are identified

      ## Verifiability

      - [ ] Every success or acceptance criterion maps to a test in this repository
      - [ ] Flow coverage covers complete use cases, not only isolated methods
      - [ ] Failure paths are covered, not only the success path
      - [ ] Rollout and rollback are described, and rollback is safe

      ## Constitution

      - [ ] Every principle this feature touches has a row in Constitution Alignment
      - [ ] Every departure from a MUST is justified in the spec, not left to the code
      - [ ] No obligation of the constitution is left as an unfilled placeholder

      ## Notes

      - Items marked incomplete require spec updates before `/speckit-plan` or `/speckit-implement`
      ```

      Keep only the block that matches the origin resolved in Gate 0: `## Inheritance` with a Product Spec, `## Origin` without one. Delete the other block from the checklist. Without a Product Spec, also delete the Technical Completeness items about architecture-document contracts and the Impact Map.

   b. **Run the validation**: review the spec against each item, determining pass or fail and quoting the relevant spec section for each failure.

      Note what this checklist deliberately does **not** ask. Implementation detail, named technologies and concrete paths are **required** here. Never remove technical content from the spec to make an item pass, and never rewrite it for a non-technical audience.

   c. **Handle validation results**:

      - **If all items pass**: mark the checklist complete and proceed to the Mandatory Post-Execution Hooks section.

      - **If items fail (excluding [NEEDS CLARIFICATION])**:
        1. List the failing items and the specific issue for each
        2. Update the spec to address each one
        3. Re-run validation until all items pass (max 3 iterations)
        4. If still failing after 3 iterations, record the remaining issues in the checklist notes and warn the user

      - **If an `## Inheritance` or `## Origin` item fails**: this is not a formatting nit. Stop and resolve it with the user before continuing — an unpinned Product Spec reference, or a spec that opens with neither section, violates the constitution and makes the spec unmergeable.

      - **If [NEEDS CLARIFICATION] markers remain**:
        1. Extract all markers from the spec
        2. **LIMIT CHECK**: if more than 3 exist, keep the 3 that most change the technical approach and make informed decisions for the rest, recording them in `Implementation Decisions`
        3. For each remaining question (max 3), present options to the user in this format:

           ```markdown
           ## Question [N]: [Topic]

           **Context**: [Quote relevant spec section]

           **What we need to know**: [Specific question from the NEEDS CLARIFICATION marker]

           **Suggested Answers**:

           | Option | Answer | Technical consequence |
           |--------|--------|-----------------------|
           | A      | [First suggested answer] | [What it means for the approach] |
           | B      | [Second suggested answer] | [What it means for the approach] |
           | C      | [Third suggested answer] | [What it means for the approach] |
           | Custom | Provide your own answer | [Explain how to provide custom input] |

           **Your choice**: _[Wait for user response]_
           ```

        4. **CRITICAL - Table Formatting**: keep pipes aligned, put spaces around cell content (`| Content |`), and use at least three dashes in the header separator.
        5. Number questions sequentially (Q1, Q2, Q3 — max 3 total)
        6. Present all questions together before waiting for responses
        7. Wait for the user to respond to all of them
        8. Replace each marker with the selected or provided answer
        9. Re-run validation

   d. **Update the checklist** after each validation iteration with the current pass/fail status.

## The Divergence Rule

This rule applies only to a spec derived from a Product Spec. A spec without one inherits nothing to diverge from; its problem and acceptance criteria are edited in the spec itself.

If, while writing the spec, a technical need contradicts something inherited — the scope, a success criterion, or a binding decision:

1. **Do not implement it and do not absorb it silently into the spec.** A silent deviation is the one thing this model does not tolerate.
2. Tell the user plainly what contradicts what, and that it requires an amendment in the product repository.
3. Record it in the `## Divergences` section of the spec, with a link to the amendment once it exists.
4. Carry on with everything that does not depend on that decision. The amendment is decided by the trio; unaffected work continues.
5. When the amendment is approved and produces a new tag, update `Pinned version` to it.

A technical difference that contradicts nothing inherited is **not** a divergence. It is an implementation decision, and it belongs in `## Implementation Decisions`.

## Mandatory Post-Execution Hooks

**You MUST complete this section before reporting completion to the user.**

Check if `.specify/extensions.yml` exists in the project root.
- If it does not exist, or no hooks are registered under `hooks.after_specify`, skip to the Completion Report.
- If it exists, read it and look for entries under the `hooks.after_specify` key.
- If the YAML cannot be parsed or is invalid, do not skip silently: tell the user that `.specify/extensions.yml` could not be read (include the parser error) and that no hooks were checked, including any mandatory (`optional: false`) hooks registered there, then continue to the Completion Report.
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- When constructing command invocations from hook command names, replace dots (`.`) with hyphens (`-`). For example, `speckit.git.commit` → `/speckit-git-commit`.
- For each executable hook, output the following based on its `optional` flag:
  - **Mandatory hook** (`optional: false`) — **You MUST emit `EXECUTE_COMMAND:` for each mandatory hook**:
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    After emitting the block above you MUST actually invoke the hook and wait for it to finish before continuing. Run it the same way you would run the command yourself in this agent/session (the invocation may differ from the literal `{command}` id shown above, e.g. a skills-mode agent runs it as `/skill:speckit-...` or `$speckit-...`). Emitting the block alone does not run the hook.
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```

## Completion Report

Report completion to the user with:
- `SPECIFY_FEATURE_DIRECTORY` — the feature directory path
- `SPEC_FILE` — the spec file path
- The origin: the inherited Product Spec and its pinned version, or "no Product Spec", so the traceability is visible without opening the file
- Checklist results summary
- Any divergence raised
- Readiness for the next phase: `/speckit-plan` or `/speckit-implement`, at the developer's choice

**NOTE:** Branch creation is handled by the `before_specify` hook (git extension). Spec directory and file creation are always handled by this command.

## Quick Guidelines

- Focus on **HOW this repository** delivers its slice. With a Product Spec the what is inherited, and restating it is a defect; without one, the what is limited to the problem and acceptance criteria of the origin section.
- Be specific and technical: name real modules, real endpoints, real events, real paths. Vagueness here becomes rework in the plan.
- Write for the engineers of this repository, not for a business audience.
- With a Product Spec, never widen the scope beyond what it covers. New scope is an amendment, not a spec section.
- Prefer a recorded decision over a question. Ask only when the answer changes the approach.
- DO NOT create any checklists embedded in the spec. That is a separate command.

### Frontend and Backend Derive Separately

One Product Spec normally produces more than one Engineering Spec, because frontend and backend live in different repositories with different constitutions. Write only this repository's slice, name the contract you need from the other side, and let the other repository specify its own. The two specs MUST pin the same version of the Product Spec.

### Done Means In Production

The definition of done is the change in production satisfying the **inherited** success criteria, or the acceptance criteria of the origin section when there is no Product Spec — not a merged pull request and not a staging deploy. Keep that in mind when writing the test strategy and the rollout section: they are what make that claim checkable.

## Done When

- [ ] The origin was resolved before anything was written: a Product Spec located, verified clean and pinned by commit or tag, or the developer's statement that there is none
- [ ] The constitution was loaded and treated as binding, with every departure justified in the spec
- [ ] Specification written to `SPEC_FILE` and validated against the engineering quality checklist
- [ ] Extension hooks dispatched or skipped according to the rules above
- [ ] Completion reported with feature directory, spec file path, origin and checklist results
