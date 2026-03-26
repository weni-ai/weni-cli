# Agent Evaluation

Agent Evaluation allows you to automatically test your Weni agents by defining test plans with steps and expected results. An LLM evaluator interacts with your agent and judges whether the responses meet the expected criteria.

## How it works

The evaluation flow follows these stages:

1. **Initialization**: The evaluator reads your test plan (`agent_evaluation.yml`)
2. **Test execution**: For each test case, the evaluator sends prompts to your agent and collects responses
3. **Judgment**: The evaluator (an LLM model via Amazon Bedrock) analyzes the conversation and determines if the expected results were observed
4. **Report**: Results are displayed in a summary table and a markdown report is saved

## Getting started

### Prerequisites

Before running evaluations, make sure you have:

- [x] Weni CLI installed and authenticated (`weni login`)
- [x] A project selected (`weni project use <project-uuid>`)
- [x] An active agent configured in your Weni project

### Initialize an evaluation plan

Create a default `agent_evaluation.yml` file in the current directory:

```bash
weni eval init
```

You can also specify a directory:

```bash
weni eval init --plan-dir <path_to_directory>
```

This generates a starter plan like:

```yaml title="agent_evaluation.yml"
evaluator:
  model: claude-haiku-4_5-global
  aws_region: us-east-1

target:
  type: weni

tests:
  greeting:
    steps:
      - Send a greeting message to the agent
    expected_results:
      - Agent responds with a friendly greeting
```

## Plan file structure

The `agent_evaluation.yml` file has three main sections:

### `evaluator`

Configures the LLM model used to judge the agent's responses.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | The evaluator model. See [available models](#available-models) below. |
| `aws_region` | string | No | AWS region for Bedrock. Defaults to `us-east-1`. |

#### Available models

| Alias | Model |
|-------|-------|
| `claude-3` | Claude 3 Sonnet |
| `claude-3_5` | Claude 3.5 Sonnet |
| `claude-3_7-us` | Claude 3.7 Sonnet |
| `claude-haiku-3_5-us` | Claude 3.5 Haiku |
| `claude-sonnet-4_5-global` | Claude Sonnet 4.5 |
| `claude-haiku-4_5-global` | Claude Haiku 4.5 (default) |
| `llama-3_3-us` | Llama 3.3 70B |

Models suffixed with `-us` use the USA cross-region inference profile. Models suffixed with `-global` use the global inference profile.

### `target`

Defines the agent being tested.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Must be `weni` for Weni agents. |

When running through the Weni CLI, the authentication token and project UUID are automatically injected from your CLI session. No additional target configuration is needed.

### `tests`

Defines the test cases. Each test has a unique key and contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `steps` | list of strings | Yes | The sequence of actions/messages to send to the agent. |
| `expected_results` | list of strings | Yes | The criteria the evaluator uses to judge the agent's responses. |

## Writing tests

### Single-turn test

A simple test with one message and one expected result:

```yaml
tests:
  greeting:
    steps:
      - Send a greeting "Hello!"
    expected_results:
      - Agent responds with a friendly greeting
```

### Multi-turn test

A test with multiple messages to verify conversation context:

```yaml
tests:
  multi_turn_conversation:
    steps:
      - Ask "What are your business hours?"
      - Follow up with "And on weekends?"
    expected_results:
      - Agent provides business hours for weekdays
      - Agent maintains context and provides weekend hours
```

### Multiple expected results

You can define multiple criteria that must all be met:

```yaml
tests:
  product_inquiry:
    steps:
      - Ask "What products do you offer?"
    expected_results:
      - Agent provides information about available products
      - Response includes clear product descriptions
      - Agent offers to help with specific product questions
```

### Error handling test

Test how the agent handles unexpected inputs:

```yaml
tests:
  error_handling:
    steps:
      - Send an unclear message "xyz123 !!!"
    expected_results:
      - Agent handles the unclear input gracefully
      - Agent asks for clarification or provides guidance
```

## Running evaluations

### Run all tests

```bash
weni eval run
```

### Run specific tests

Use `--filter` to run only selected tests (comma-separated):

```bash
weni eval run --filter "greeting,product_inquiry"
```

### Verbose output

Use `--verbose` to see detailed reasoning for each test result:

```bash
weni eval run --verbose
```

### Custom plan directory

If your plan file is in a different directory:

```bash
weni eval run --plan-dir <path_to_directory>
```

## Understanding results

After running, the CLI displays a results table:

| Test | Status |
|------|--------|
| greeting | PASS |
| product_inquiry | PASS |
| error_handling | FAIL |

A markdown summary report is automatically saved to the `evaluation_results/` directory with a timestamp (e.g., `summary_20260326_190242.md`).

When using `--verbose`, the reasoning column shows the evaluator's explanation for each test verdict.

## Complete example

```yaml title="agent_evaluation.yml"
evaluator:
  model: claude-haiku-4_5-global
  aws_region: us-east-1

target:
  type: weni

tests:
  greeting:
    steps:
      - Send "Hello, good morning!"
    expected_results:
      - Agent responds with a friendly greeting
      - Agent introduces itself or explains its capabilities

  product_inquiry:
    steps:
      - Ask "What products do you have available?"
    expected_results:
      - Agent provides information about available products
      - Response includes clear product descriptions or categories

  multi_turn_conversation:
    steps:
      - Ask "What are your business hours?"
      - Follow up with "And on weekends?"
    expected_results:
      - Agent provides business hours for weekdays
      - Agent maintains context and provides weekend hours
      - Responses are coherent and contextual

  error_handling:
    steps:
      - Send an unclear message "xyz123 !!!"
    expected_results:
      - Agent handles the unclear input gracefully
      - Agent asks for clarification or provides guidance
```

## Troubleshooting

**"Could not find agent_evaluation.yml"**

- Make sure you ran `weni eval init` first, or specify the correct directory with `--plan-dir`.

**Authentication errors (401)**

- Run `weni login` to refresh your token.
- Verify you have a project selected with `weni project current`.

**Evaluation timeout**

- Your agent may need more time to respond. Check if the agent is active and properly configured in the Weni platform.

**Tests failing unexpectedly**

- Use `--verbose` to see the evaluator's reasoning.
- Make sure your `expected_results` are clear and specific.
- Verify your agent is responding correctly by testing it manually in the Weni platform first.
