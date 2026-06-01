# Active Agent Test Run

`weni run` for Active Agents lets you execute the **PreProcessor + Rules** pipeline of an active agent against a curated set of test cases, all from your local source tree. The CLI packages your code, the backend creates an ephemeral Lambda, runs each test case against it, streams the results back, and tears the Lambda down — all without touching anything in your project's deployed Gallery.

Use this command to:

- Iterate on a PreProcessor or Rule without doing a full `weni project push`
- Validate the end-to-end flow (PreProcessor → Rule → template selection) against a real backend
- Debug a specific test case by inspecting the Lambda response and CloudWatch logs

!!! note "How it differs from `weni run` for tools"
    For passive agents (Tools), the CLI uploads a single tool zip and the backend runs each test as an isolated Lambda invocation in the Bedrock format. For active agents, the CLI uploads **the preprocessor folder + every rule folder** and the backend invokes the active Lambda template. The `tool_key` argument is **not used** for active agents; the CLI auto-detects the agent type from the definition file.

## Prerequisites

You need an Active Agent already implemented locally. If you are new to active agents, read the [Active Agents](../core-concepts/active-agents.md) page first.

Concretely, your project tree should look like this:

```
your-project-name/
├── pre_processors/
│   └── processor/
│       ├── processing.py
│       └── requirements.txt
├── rules/
│   ├── rule_one/
│   │   ├── main.py
│   │   └── requirements.txt
│   └── rule_two/
│       └── main.py
├── agent_definition.yaml
└── test_definition.yaml   # (new) — created next to agent_definition.yaml
```

## Writing the `test_definition.yaml`

For active agents, the test definition file lives **next to `agent_definition.yaml`** (the agent root), not inside a rule folder. Each top-level key under `tests:` is a test case name that will appear in the CLI output.

### Minimal example

```yaml title="test_definition.yaml"
tests:
  order_paid:
    payload:
      OrderId: "1621590779140-01"
      State: "payment-approved"
      Domain: "Marketplace"
```

This is enough for the CLI to build the agent, create a Lambda, and run the case. Optional fields let you simulate richer scenarios.

### Full reference

Under each test case you can declare up to seven fields. Only `payload` is required.

`payload`
:   **Required.** Arbitrary dictionary with the raw input that the PreProcessor consumes. The keys are **agent-specific** — open your agent's `processing.py` to see which keys it reads via `context.payload.get(...)`. Examples in the wild:

    - VTEX webhook for order events: `OrderId`, `State`, `Domain`
    - Cart abandonment events: `order_form_id`, `phone_number`, `cart_items`
    - Custom integrations: whatever your code expects

`params`
:   Optional dictionary delivered to `PreProcessorContext.params`. Used by integrations that pass auxiliary parameters alongside the payload. Most of the official VTEX agents do not consume this field, but it is part of the contract.

`credentials`
:   Optional dictionary delivered to `PreProcessorContext.credentials`. The official VTEX agents typically read everything from `project` instead, but you can use this for custom credentials consumed via `context.credentials.get("api_key")`.

`project`
:   Recommended dictionary with project metadata. In production this is populated by the orchestrator; for `weni run` you populate it to simulate the environment. Common fields:

    - `uuid` — Weni project UUID. Consumed by the PreProcessor via `context.project.get("uuid")` for the agent's own internal logic (logging, populating output data, etc.). **This field does NOT determine the JWT used for authentication.** The JWT is always generated from the project currently selected with `weni project use` (this matches the behaviour of `weni run` for passive Tools). If you need to authenticate against a different project, run `weni project use <project_uuid>` before invoking the tests.
    - `vtex_account` — VTEX account identifier registered in retail-setup (it is **not** the VTEX hostname). Required for agents that integrate with VTEX (the project on staging/production must have a matching VTEX integration configured).
    - `country_phone_code` — for agents that normalize phone numbers (e.g. `"55"` for Brazil).
    - `channel_uuid` — used by some agents (e.g. cart abandonment).
    - `auth_token` — JWT used by the agent to call internal Weni services. **You don't need to set this manually.** The backend generates a short-lived JWT (based on the project from `weni project use`) and injects it automatically before invoking the Lambda.

`project_rules`
:   Optional list of **custom project rules** (rules supplied inline as Python source, not packaged with the agent). Each item has `template` plus `source` with code that defines a class inheriting from `weni.rules.Rule`. Useful for testing rules that will be created dynamically by the user in the Nexus, before promoting them to a permanent rule folder.

    ```yaml
    project_rules:
      - template: "premium_customer_alert"
        source: |
          from weni.rules import Rule
          class PremiumCustomer(Rule):
              def execute(self, data):
                  return data.data.get("price", 0) > 100000
              def get_template_variables(self, data):
                  return {"1": data.data.get("name")}
    ```

`ignored_official_rules`
:   Optional list of rule keys (as defined in the agent's `rules` block of `agent_definition.yaml`) that should be **skipped** in this test case. Useful for forcing a specific rule not to match in order to validate fallback behaviour.

    ```yaml
    ignored_official_rules: ["PaymentApproved", "OrderInvoiced"]
    ```

`global_rule`
:   Optional string with Python source defining a function called `global_rule(data)`. Evaluated **before** any project or official rule. If it returns `False`, no rule is evaluated and the result is `GLOBAL_RULE_NOT_MATCHED`. Use this to implement circuit-breakers (e.g. skip everything if the order value is below a threshold).

    ```yaml
    global_rule: |
      def global_rule(data):
          return data.data.get("price", 0) > 10000
    ```

### How the test case becomes a Lambda event

For each test case, the CLI assembles the event below and the backend invokes the agent's Lambda with it:

```json
{
  "payload":                  { ... },
  "params":                   { ... },
  "credentials":              { ... },
  "project":                  { ..., "auth_token": "<JWT auto-injected>" },
  "project_rules":            [ ... ],
  "ignored_official_rules":   [ ... ],
  "global_rule":              "<source or null>"
}
```

Inside the Lambda, this is converted into a `PreProcessorContext` consumed by your agent's `PreProcessor.process(context)` method, and the resulting `ProcessedData` flows through the rule evaluation pipeline (`global_rule` → `project_rules` → official rules with `ignored_official_rules` skipped).

## Running the tests

```
weni run [agent_definition_file] [agent_key] [-f FILE] [-v]
```

A practical example, assuming the agent definition above:

```
weni run agent_definition.yaml my_active_agent
```

Note that **`tool_key` is omitted** — the CLI detects from `agent_definition.yaml` that this is an active agent (it has a `rules` block) and switches to the active flow automatically.

Add `-v` (or `--verbose`) for richer output:

```
weni run agent_definition.yaml my_active_agent --verbose
```

### Choosing a test file

- Use `-f/--file` to specify a test definition YAML at any path.
- If `-f` is omitted, the CLI looks for `test_definition.yaml` **next to the agent definition file** (same directory as `agent_definition.yaml`).

## Reading the results

The CLI renders a live table while tests run. When all are finished, the table summarises the outcome of each case.

Status icons map to the `ResponseStatus` enum returned by the active Lambda template:

| Icon | Status | Meaning |
|---|---|---|
| :white_check_mark: | `RULE_MATCHED` | A rule fired and selected a template |
| :yellow_circle: | `RULE_NOT_MATCHED` | All rules evaluated, none matched (no error) |
| :yellow_circle: | `GLOBAL_RULE_NOT_MATCHED` | The `global_rule` returned `False`, skipping the rest |
| :x: | `PREPROCESSING_FAILED` | The PreProcessor raised an unhandled exception |
| :x: | `CUSTOM_RULE_FAILED` | A `project_rules` item raised an unhandled exception |
| :x: | `OFFICIAL_RULE_FAILED` | An official rule raised an unhandled exception |
| :x: | `GLOBAL_RULE_FAILED` | The `global_rule` raised an unhandled exception |

The `Result` column also shows, when applicable: `template=<name>`, `urn=<contact_urn>`, and a short `error=...` diagnostic when the Lambda template populated the error field.

### Verbose output

With `--verbose`, the CLI prints two panels per test case after the table:

- **Response** — the full `LambdaResponse` returned (status, template, template_variables, contact_urn, error).
- **Logs** — stdout/stderr captured from the Lambda via CloudWatch Tail. Includes `print(...)` statements from your PreProcessor and rules — very useful to pinpoint which guard / gate caused a `RULE_NOT_MATCHED`.

## Authentication and ephemeral Lambdas

`weni run` is **isolated by design**:

- No messages are dispatched to channels.
- The Nexus orchestrator is **not** invoked.
- A fresh Lambda is created per run, named `cli-<uuid>`, and deleted in the `finally` block once all test cases complete (or as soon as an error occurs).
- The backend generates a short-lived JWT based on the project selected via `weni project use` and injects it into `project.auth_token` before invoking the Lambda. To run tests against a different project, switch with `weni project use <project_uuid>` first and re-run.

## Common error patterns

`"VTEX account not defined for project."` in the verbose Logs panel
:   The project linked to the JWT does not have a VTEX integration configured in `retail-setup`. Check that the project_uuid (either from `weni project use` or `project.uuid` in the YAML) is correct and that the integration has been provisioned. Run `weni project current` to see which project the CLI is currently scoped to.

`"Failed to get default test definition file: test_definition.yaml next to the agent definition"`
:   Either create a `test_definition.yaml` next to `agent_definition.yaml`, or pass an explicit path with `-f`.

`"Invalid test definition for active agent: Test <name> is missing required field 'payload'"`
:   Every test case must have a `payload` dictionary (other fields are optional). Make sure the YAML structure follows the reference above.

`"At least one active agent resource (preprocessor + rules) is required"`
:   The backend received the active flow request without any preprocessor/rule files. This usually means the CLI was an older version that doesn't yet support the active flow; upgrade with `pip install -U weni-cli`.

## Iterating locally

A typical loop:

1. Edit your `processing.py` or rule's `main.py`
2. Add or tweak a case in `test_definition.yaml`
3. Run `weni run agent_definition.yaml <agent_key> --verbose`
4. Inspect the Lambda response and logs; iterate

No `weni project push` is required between iterations — the CLI uploads your current source tree on every run.
