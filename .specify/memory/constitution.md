<!--
Sync Impact Report:
- Version change: none (unfilled template) → 1.0.0
- Modified principles: none (first generation)
- Added principles:
  I. Version Control and Review
  II. Security and Secrets
  III. Observability and Diagnosable Errors (root Observability + backend Diagnosable Errors)
  IV. Code Clarity and Language
  V. Proportional Design
  VI. Explicit Over Clever
  VII. Contained Changes
  VIII. Verification Integrity
  IX. Tests Exercise Flows
  X. Versioned Contracts and Compatible Data Evolution (root Versioned Contracts + backend Backward-Compatible Data Evolution)
  XI. Specification Traceability
  XII. No Silent Divergence
  XIII. Never Trust External Input
  XIV. Explicit, Scoped Authorization
  XV. Fail Gracefully and Predictably
  XVI. Bounded Retry Over REST
  XVII. Bounded Load and Scalability
  XVIII. Commit Messages
  XIX. Changelog Maintenance
- Added sections: Technology Stack and Quality Gates; Development Workflow; Governance
- Removed sections: none
- Templates requiring updates: none (.specify/templates/* left untouched; plan-template
  "Constitution Check" gates resolve against the principles above)
- Follow-up TODOs:
  - TODO(BRANCH_PROTECTION): confirm on GitHub that `main` requires one approved review
    and a green CI run, and blocks direct pushes (Principle I). Not verifiable from the repo.
- Known compliance gaps found while generating (existing code, not fixed here):
  - `.github/workflows/ci.yaml` triggers only on `push`; no dependency vulnerability scan
    runs in CI (Principles I, II).
  - `weni_cli/wsgi.py` binds the SSO callback server to `0.0.0.0` and accepts any `code`
    without an OAuth `state` check (Principles XIII, XIV).
  - `CLIClient` streaming and default requests use a `(10, None)` timeout, so reads can
    block indefinitely (Principle XV).
  - `Store.set` rewrites `~/.weni_cli` in place, non-atomically (Principle XV).
  - No retry policy exists for transient failures on idempotent API calls (Principle XVI).

Provenance:
- Source: weni-ai/vtex-cx-engineering-constitutions (main)
- Files: base-constitution.md, backend/base-constitution.md
- Domains: backend
- Project layer: weni-cli (Python CLI, Click/rich-click, requests, local Flask/Waitress SSO callback)
-->

# Weni CLI Constitution

Weni CLI (`weni`) is a Python command-line tool, published to PyPI, that authenticates
users against Weni's Keycloak and manages projects, agents, tools, channels, ticketers,
and agent evaluations through the Weni, Nexus, and CLI backend APIs. The backend
principles below are instantiated for a client-side process that talks to remote APIs
and runs a short-lived local HTTP server for the SSO callback. Where a backend article
cannot apply to a CLI, the exception and its reason are stated in that article.

## Core Principles

### I. Version Control and Review

All code MUST enter `main` through a pull request. A merge MUST require at least one
approved review and a green CI run (`.github/workflows/ci.yaml`: pytest, flake8, mypy
across the supported Python matrix). Direct pushes to `main` MUST be blocked via GitHub
branch protection. Releases MUST be produced only by pushing a SemVer tag that triggers
`.github/workflows/publish.yaml`; packages MUST NOT be published manually.

**Rationale:** the policy is only real when enforced by the platform, not by trust. Peer
review and a protected `main` keep history auditable and prevent unreviewed changes from
reaching every user who runs `pip install weni-cli`.

### II. Security and Secrets

Secrets MUST never be committed to the repository. CI and release credentials
(`PYPI_TOKEN`, `CODECOV_TOKEN`, `GITHUB_TOKEN`) MUST be provided through GitHub Actions
secrets and injected at runtime. The user's access token stored in `~/.weni_cli` MUST NOT
be printed, logged, included in error messages, or sent to any host other than the
configured Weni endpoints; that file SHOULD be readable only by its owner. Secret values
returned by the platform (tokens, passwords, webhook secrets, keys) MUST be masked in
command output unless the user explicitly opts in (e.g. `--show-secrets`). Access MUST
follow least privilege by default. Dependencies MUST come only from trusted sources
(PyPI, pinned through `poetry.lock`) and MUST be checked for known vulnerabilities.

**Rationale:** leaked credentials and untrusted dependencies are among the most common
and most damaging breaches; a CLI runs on developer machines and in their CI, so a leak
from this tool exposes every project the user can reach.

### III. Observability and Diagnosable Errors

Diagnostic output MUST be structured and MUST never contain secrets or sensitive personal
data. Errors MUST NOT be silently swallowed: a caught failure MUST either be handled
explicitly as expected control flow or reported to the user with context and a non-zero
exit code. When the platform returns a correlation or request identifier, the CLI MUST
surface it in the error so the failure can be traced across components. Every error
reported to an error-tracking or telemetry system, if one is introduced, MUST carry the
project identifier, account identifier, user identifier, and correlation identifier;
those identifiers MUST be opaque, and names, e-mail addresses, phone numbers, or
government identifiers MUST NOT be attached under any circumstance.

**Rationale:** structured, privacy-safe diagnostics make support requests answerable
without reproducing them, while forbidding silent catch-all handlers prevents failures
from disappearing. Opaque identifiers give investigations the filtering they need
without exposing personal data.

### IV. Code Clarity and Language

All code, identifiers, comments, CLI help text, and technical documentation (`docs/`,
`README.md`, `CHANGELOG.md`) MUST be written in English; domain-specific terms or
acronyms that only carry meaning in their original language (e.g. `cep`) MAY remain
untranslated. Code MUST prioritize clarity over brevity or cleverness. Comments MUST
explain *why* a non-obvious decision was made and MUST NOT restate *what* the code
already expresses; code that needs a comment to explain what it does SHOULD be rewritten.
Dead branches and commented-out code MUST NOT be committed.

**Rationale:** a shared language and self-explanatory code let any engineer across teams
read, review, and maintain the repository without hidden context; narrative comments and
dead code drift out of sync and mislead readers.

### V. Proportional Design

Every change MUST use the simplest design that satisfies the current specification
within the established architecture: Click commands in `weni_cli/cli.py` delegating to
handlers in `weni_cli/commands/`, HTTP access in `weni_cli/clients/`, input validation in
`weni_cli/validators/`, packaging in `weni_cli/packager/`, and local configuration in
`weni_cli/store.py`. Abstractions, indirection layers, extension points, or configuration
flags MUST NOT be introduced for hypothetical future needs when only one concrete use
case exists. Every encoded decision — a business rule, a default URL, a store key — MUST
have a single source of truth (e.g. `STORE_*` constants in `store.py`); incidental
duplication MAY remain local when extracting it would create premature coupling. Root
causes MUST be fixed rather than masked, and redundant checks SHOULD NOT repeat
invariants already enforced by types, validators, or the API.

**Rationale:** speculative abstractions, pass-through wrappers, and redundant defensive
checks add cost without solving a real problem today. A single source of truth for each
decision prevents behavioral and environment drift.

### VI. Explicit Over Clever

Hidden side effects and implicit control flow MUST NOT be introduced to save lines. Any
literal that carries domain or operational meaning — a timeout, a port, a retry count, a
size or length limit, an API path version — MUST be a named constant rather than an
inline value; literals with no meaning beyond their own value (an index of `0`, an
increment of `1`) are exempt.

**Rationale:** hidden side effects and unexplained magic numbers obscure operational
limits from reviewers, whereas explicit control flow and named constants make behavior
auditable at the call site.

### VII. Contained Changes

A change MUST be limited to the context it was asked to address. Refactoring, renaming,
reformatting, or behavior adjustments outside that context MUST NOT ride along; each
belongs to its own change. A change that stays within scope MAY span several commits,
each of which remains atomic (Principle XVIII).

**Rationale:** a change that reaches beyond its stated scope is a change nobody reviewed
on purpose; it hides the intended fix inside unrelated edits and turns a revert into a
choice between losing the fix and keeping an unrelated regression.

### VIII. Verification Integrity

Automated checks and tests MUST verify real behavior and MUST fail when the behavior,
contract, or guard they cover regresses. A test MUST NOT mock, stub, or bypass the
subject, validator, permission check, or boundary contract it claims to prove. The
per-change suite (`poetry run pytest`) MUST be deterministic and hermetic: Weni, Nexus,
Keycloak, and any third-party HTTP calls MUST be stubbed at the HTTP boundary (e.g.
`requests_mock`), and the user's real `~/.weni_cli` MUST NOT be read or written by tests.
Suites that intentionally exercise real dependencies MAY reach them only when labeled as
such, run in a stage separate from the per-change suite, and never target production
projects. Failing checks, flake8 rules, mypy errors, or coverage gates MUST NOT be
silenced or skipped (`# noqa`, `# type: ignore`, `pytest.skip`, `# pragma: no cover`)
without an explicit justification next to the suppression.

**Rationale:** a green suite that mocks away the mechanism under test or disables quality
gates creates false confidence. Hermetic boundaries keep the suite fast, reproducible,
and independent of platform outages or a developer's local login state.

### IX. Tests Exercise Flows

Every command MUST have at least one test that runs it through its real entry point
(Click's `CliRunner` against the `weni` command group), its validators, its HTTP client,
and its effect on local state or command output. Isolated unit tests (e.g. under
`weni_cli/*/tests/`) SHOULD be used for edge cases and input variations that are
expensive to reach through the whole flow, but MUST NOT be a command's only coverage.
Every command flow MUST cover its success path and its failure paths; commands that
require authentication or a selected project MUST also cover refusal paths — no token,
no project selected, and `401`/`403` responses from the API — proving the command exits
non-zero with a clear message and leaves stored configuration unchanged.

**Rationale:** a suite made only of isolated method tests can be green while the
composition of argument parsing, validation, HTTP calls, and error handling is broken.
Exercising the real entry point across happy, error, and refusal paths proves the
behavior users actually run.

### X. Versioned Contracts and Compatible Data Evolution

The public interface of this package — command and subcommand names, options and flags,
exit codes, machine-readable output, the agent/channel/ticketer definition YAML schemas,
and importable Python APIs — MUST be versioned following SemVer through the `version`
field in `pyproject.toml`. Changes MUST be backward compatible within a major version or
ship with an announced deprecation path: a deprecated command, option, or schema field
MUST emit a warning for at least one minor release before removal in the next major.
Silent breaking changes MUST NOT be introduced. Persisted local data (`~/.weni_cli` keys)
MUST remain readable by the new version: renaming or removing a store key MUST follow an
expand-and-contract sequence (read old and new, write new, drop old in a later major).

**Rationale:** users and their CI pipelines script against this CLI and keep definition
files and config across upgrades; explicit versioning, deprecation warnings, and
compatible data evolution give them a predictable path to adapt without broken builds or
a forced re-login.

### XI. Specification Traceability

An engineering spec (`specs/<feature>/spec.md`) either derives from a product spec or
originates in engineering. Both are regular paths; neither requires a justification, and
either may follow the full or the lite cycle.

When the change has a product spec, the engineering spec MUST derive from exactly one
approved product spec and MUST reference it through an immutable, pinned version (commit
or tag) — a mutable URL or ID alone MUST NOT be used. The product spec MUST exist and be
tagged before its engineering spec is created. An engineering spec MUST NOT redefine the
"what" it inherits: problem, scope, success criteria, and binding decisions belong to the
product spec. A technical architecture document SHOULD be produced for non-trivial
features; when it exists it MUST be linked from the engineering spec, also pinned by
commit/tag, but its absence MUST NOT block the engineering spec.

An engineering spec derived from a product spec MUST open with an inheritance section in
exactly this format:

```
## Inheritance from Product Spec
- Product Spec: <title> — <URL>
- Pinned version: <commit/tag>
- Architecture doc: <none | URL + commit/tag>
- Inherited binding decisions: <short list>
- Scope of this spec: <slice implemented by this repo>
- Divergences: <none | link to amendment>
```

An engineering spec without a product spec states its own "what" and MUST open with an
origin section in exactly this format:

```
## Origin Without Product Spec
- Product Spec: none
- Problem: <what is wrong or missing, in one or two sentences>
- Acceptance criteria: <observable outcomes that prove the change is done>
```

**Rationale:** traceability from intent to execution keeps decisions auditable. Pinning
the product spec guarantees every team implements the same version of a feature; when a
change is born in engineering (a fix, technical debt), its own problem and acceptance
criteria are what it is verified against. The fixed opening format keeps the origin
machine-checkable across repositories.

### XII. No Silent Divergence

When a technical need contradicts something inherited from the product spec — scope,
success criteria, or a binding decision — the divergence MUST NOT be implemented silently
in code. It MUST be raised as an amendment in the product repository and recorded in the
`Divergences` field of the engineering spec's inheritance section, linking to that
amendment. Once the amendment is approved and tagged, the engineering spec's
`Pinned version` MUST be updated to it. A technical difference that contradicts nothing
inherited is an implementation decision and MUST live in the engineering spec. This
principle applies only to engineering specs derived from a product spec.

**Rationale:** in a federated model where the product spec is the single source of
truth, a silent code deviation makes intent and implementation drift apart with no audit
trail; amendments keep every decision traceable to an agreed change.

### XIII. Never Trust External Input

Everything that enters the CLI from outside its own code MUST be treated as potentially
malicious, incomplete, or incorrect until validated: command arguments, definition YAML
files, tool source paths and `requirements.txt` files, values read from `~/.weni_cli`,
HTTP responses from platform APIs, and requests received by the local SSO callback
server. Definition files MUST be validated for type, format, range, and business rules
in `weni_cli/validators/` before any API call. External input MUST NOT be interpolated
directly into shell commands, file paths outside the intended project directory, or
unvalidated outbound URLs; YAML MUST be parsed with a safe loader. The SSO callback MUST
verify the authenticity of the redirect (an OAuth `state` value bound to the login
attempt), reject replayed or unexpected requests, accept connections only from the local
machine, and compare secrets in constant time, before any side effect such as storing a
token.

**Rationale:** definition files and tool folders are often copied from others, the local
callback port is reachable by any process (or network peer, if bound broadly), and
platform responses cross a trust boundary. Validating and parameterizing inputs before
use prevents path traversal, command injection, login CSRF, and token injection that no
later check can undo.

### XIV. Explicit, Scoped Authorization

Authorization is enforced by the Weni platform APIs; the CLI MUST NOT be treated as an
authorization layer and MUST NOT attempt to work around a `401`/`403`. Commands acting on
a project MUST send the project scope explicitly and SHOULD check project permission
(`check_project_permission`) before uploading packages or performing destructive
actions. Destructive commands (delete, deactivate) MUST require confirmation unless the
user explicitly passes `--yes`.

Any HTTP surface this repository exposes — today only the local SSO callback in
`weni_cli/wsgi.py` — MUST deny by default, expose only the routes and HTTP methods its
contract requires, and, because it is reachable without an authenticated user, MUST rely
on a check dedicated to that endpoint (the OAuth `state` binding) whose justification is
recorded in the engineering spec that introduces or changes it. Any background worker or
long-running process added to this repository MUST re-verify scope rather than trusting
payloads blindly.

If any server component built with Django REST Framework is added to this repository,
`IsAuthenticated` and `AllowAny` MUST NOT be used under any circumstance: not in
`permission_classes`, not in the `@permission_classes` decorator, not in
`DEFAULT_PERMISSION_CLASSES`, not composed through `&` or `|`, and not as a base class. A
custom permission that unconditionally grants access is equally forbidden, and
`DEFAULT_PERMISSION_CLASSES` MUST be set explicitly.

**Rationale:** a valid token proves identity, not the right to touch a given project.
Keeping authorization on the server, sending scope explicitly, and confirming
destructive actions protects tenants from mistakes in the client; keeping the local
callback closed and bound to a dedicated check prevents it from becoming an open door to
the user's session. Naming the forbidden DRF classes keeps the rule mechanically
checkable should a server component ever appear.

### XV. Fail Gracefully and Predictably

Every call to an external dependency (Weni, Nexus, Keycloak, CLI backend, package
indexes) MUST have explicit connect and read timeouts defined as named constants and
MUST NOT block indefinitely; long-running streams MUST bound their idle read time.
Multi-step writes that must succeed or fail together MUST be atomic: updates to
`~/.weni_cli` MUST be written to a temporary file and atomically replaced so an
interrupted write cannot corrupt the user's configuration. Failures MUST be handled
explicitly and surfaced as consistent, human-readable error messages with a non-zero exit
code — never as unhandled tracebacks or leaked internal details (tokens, raw request
headers).

**Rationale:** networks fluctuate and APIs go down without warning. Timeouts, atomic
writes, and predictable error boundaries keep a failing dependency from hanging a user's
terminal or CI job, corrupting their login state, or exposing internals.

### XVI. Bounded Retry Over REST

When the CLI propagates data to platform APIs over REST, a transient failure — connection
error, request timeout, HTTP 5xx, or HTTP 429 — MUST be retried rather than dropped, and a
4xx that reflects a defect in the request MUST NOT be retried. Retry MUST only be applied
to operations that are idempotent (`GET`, `PUT`, `DELETE`) or protected by a
deduplication key. Every retry policy MUST define a maximum number of attempts and a
backoff strategy as named constants; unbounded retry MUST NOT be used. When attempts are
exhausted, the failure MUST be reported with context and a non-zero exit code so the user
can recover by re-running the command — it MUST NOT be silently discarded.

*Project exception:* the base rule requires non-idempotent operations to be made
idempotent rather than left without retry. This repository does not own the server
endpoints, so it cannot make them idempotent. Non-idempotent calls without a
deduplication key (e.g. `push_agents`, `create_channel`, `create_ticketer`) MUST NOT be
retried automatically; they MUST fail fast with a recoverable message, and the missing
idempotency SHOULD be raised with the owning API team.

**Rationale:** transient failures are far more common than permanent ones, so retrying
idempotent calls keeps commands reliable. Retrying a rejected request only adds load, and
retrying a non-idempotent push duplicates agents or channels instead of repairing the
failure. Bounds keep the CLI from amplifying load on a platform that is already degraded.

### XVII. Bounded Load and Scalability

List commands MUST consume the API's pagination (follow `next`) rather than requesting
unbounded collections, and per-item fan-out requests SHOULD be avoided whenever the API
offers a bulk or filtered endpoint. Request handlers in the local server MUST NOT spawn
OS processes or perform long-running work. Any cache introduced for platform data MUST
key entries by project UUID (and user, when user-specific), define an explicit TTL, and
be invalidated by every command that mutates the cached data. Large uploads (tool
packages) MUST stay within the size limits the platform declares.

*Project exception:* the stateless-service and peak-load-declaration rules of the backend
base apply to horizontally scaled services. This repository ships no such service: the
CLI is a single-user process whose per-user state in `~/.weni_cli` is intentional, and
the SSO callback server lives only for the duration of `weni login`. Those rules become
mandatory for any long-running service added to this repository, whose engineering spec
MUST then declare its expected peak load.

**Rationale:** the CLI's load lands on shared platform APIs; paginating, avoiding N+1
fan-out, and scope-isolated caches keep one user's command from degrading the platform or
showing another project's data. Stating the exception explicitly prevents server rules
from being misapplied or silently ignored.

### XVIII. Commit Messages

Commits MUST follow Conventional Commits format: `<type>: <description>`. Allowed types:
`feat`, `fix`, `docs`, `refactor`, `test`, `chore`. The description MUST be imperative,
specific, and no longer than 50 characters. Commits MUST be atomic: one logical change
per commit.

**Rationale:** conventional commits enable automated changelog generation and semantic
versioning; atomic commits simplify bisecting, reverting, and reviewing.

### XIX. Changelog Maintenance

`CHANGELOG.md` MUST follow Keep a Changelog format. Every user-facing change MUST appear
under the appropriate category (Added, Changed, Deprecated, Removed, Fixed, Security) in
the entry for its release, referencing the pull request. The version in
`pyproject.toml`, the changelog heading, and the release tag MUST match and follow SemVer.

**Rationale:** the changelog is the release documentation for PyPI users; keeping it
aligned with the package version and tag gives predictable upgrade expectations.

## Technology Stack and Quality Gates

- **Language and runtime:** Python `^3.10`; CI MUST pass on every version in the
  `ci.yaml` matrix (currently 3.10–3.13).
- **Packaging:** Poetry (`pyproject.toml` + `poetry.lock`); entry point
  `weni = "weni_cli.cli:cli"`. New runtime dependencies MUST be justified in the plan and
  pinned via the lockfile.
- **CLI framework:** `rich-click` / `rich` for commands and output; `requests` for HTTP;
  Flask + Waitress only for the local SSO callback.
- **Formatting and linting:** `black` (line length 119) and `flake8` (`.flake8`) MUST
  pass; `mypy` MUST pass on the whole repository.
- **Tests:** `pytest` with `pytest-mock` and `requests-mock`; command-flow tests in
  `tests/`, unit tests in `weni_cli/<module>/tests/`. Coverage is reported to Codecov on
  every CI run; coverage MUST NOT decrease for changed modules without justification.
- **Documentation:** user-facing behavior changes MUST update `docs/` (MkDocs) and, when
  relevant, `README.md` in the same pull request.

## Development Workflow

1. Create or update the engineering spec under `specs/<feature>/` with the opening
   section required by Principle XI.
2. Produce the plan; its Constitution Check MUST list every principle the change touches
   and justify any exception.
3. Implement within scope (Principle VII), with command-flow tests covering success,
   failure, and refusal paths (Principle IX).
4. Run `poetry run black --check .`, `poetry run flake8 weni_cli`, `poetry run mypy .`,
   and `poetry run pytest` locally before opening the pull request.
5. Update `CHANGELOG.md` and bump `pyproject.toml` for user-facing changes (Principles X
   and XIX); release by tagging after merge.

## Governance

This constitution supersedes conflicting local practices for this repository. Its
content derives from the VTEX CX engineering base constitution (root) and the backend
base constitution; on conflict, the root prevails over the domain, and the domain
prevails over this project's instantiation. Project-level exceptions MUST be written into
the affected principle with their justification, as done in Principles XVI and XVII.

Amendments are made through a pull request that updates this file and its Sync Impact
Report, and they follow SemVer: MAJOR when a principle is removed or redefined in an
incompatible way, MINOR when a principle or section is added or materially expanded, and
PATCH for clarifications and wording fixes. When the upstream base constitutions change,
this file SHOULD be regenerated with `setup-engineering`, preserving project exceptions
that still apply.

Every plan MUST pass a Constitution Check against these principles, and reviewers MUST
verify compliance during pull request review. `/speckit.analyze` treats any conflict with
a `MUST` as CRITICAL.

**Version**: 1.0.0 | **Ratified**: 2026-11-26 | **Last Amended**: 2026-11-26
