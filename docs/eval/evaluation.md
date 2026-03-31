# Agent Evaluation

Agent Evaluation allows you to automatically test your Weni agents by defining test plans with steps and expected results. An evaluator interacts with your agent and judges whether the responses meet the expected criteria.

## How it works

The evaluation flow follows these stages:

1. **Initialization**: The evaluator reads your test plan (`agent_evaluation.yml`)
2. **Test execution**: For each test case, the evaluator sends prompts to your agent and collects responses
3. **Judgment**: The evaluator analyzes the conversation and determines if the expected results were observed
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
tests:
  greeting:
    steps:
      - Send a greeting message to the agent
    expected_results:
      - Agent responds with a friendly greeting
```

You only need to define your test scenarios. The evaluator model and authentication are automatically handled by the Weni CLI.

## Plan file structure

The `agent_evaluation.yml` file contains your test definitions. Each test has a unique key and contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `steps` | list of strings | Yes | The sequence of actions/messages to send to the agent. |
| `expected_results` | list of strings | Yes | The criteria used to judge the agent's responses. |

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
