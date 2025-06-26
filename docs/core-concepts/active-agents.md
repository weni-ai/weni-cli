# Active Agents

## Overview

Active Agents are designed to proactively engage based on predefined rules and conditions. Unlike Passive Agents that primarily react to user input, Active Agents can initiate actions or communications when specific criteria are met, often triggered by changes in data or system events.

The command to deploy an Active Agent remains the same:
`weni project push agent_definition.yaml`

However, the structure of the `agent_definition.yaml` is different to accommodate the rule-based behavior and pre-processing capabilities.

## Creating an Active Agent

An Active Agent's definition is also done using a YAML file. Here's an example of the structure for an Active Agent:

```yaml title="agent_definition.yaml"
agents:
  my_agent:
    name: "Status do Pedido"
    description: "Agente de exemplo"
    rules:
      status_aprovado:
        display_name: "Status Aprovado"
        template: "template_status_aprovado"
        start_condition: "Quando o status estiver 'aprovado'"
        source:
          entrypoint: "main.StatusAprovado"
          path: "rules/status_aprovado"
      status_invoiced:
        display_name: "Status Invoiced"
        template: "template_status_invoiced"
        start_condition: "Quanto o status estiver 'invoiced'"
        source:
          entrypoint: "main.StatusInvoiced"
          path: "rules/status_invoiced"
    pre_processing:
      source:
        entrypoint: "processing.PreProcessor"
        path: "pre_processors/processor"
      result_examples_file: "result_example.json"
```

### YAML Elements

Below are the key elements specific to or different in Active Agent definitions:

`agents.<agent_id>`
:    The unique identifier for your agent.

    `name`
    :   The display name of your agent.  
        **Limit**: :octicons-alert-24: Maximum of 128 characters.

    `description`
    :   A description of the agent's purpose and capabilities.

    `rules`
    :   A dictionary defining the rules that trigger the agent's actions. Each key within `rules` is a unique rule ID.

        `rules.<rule_id>.display_name`
        :   The human-readable name for the rule.

        `rules.<rule_id>.template`
        :   The template to be used when this rule is triggered. (Further details on templates might be needed here or in a separate section).

        `rules.<rule_id>.start_condition`
        :   A description of the condition that must be met for this rule to activate.

        `rules.<rule_id>.source`
        :   Defines the code to be executed when the rule is triggered.
            `entrypoint`: The specific class and method (e.g., `main.StatusAprovado`) that will be executed.
            `path`: The directory path where the rule's code is located (e.g., `rules/status_aprovado`).

    `pre_processing`
    :   Defines a pre-processing step that can transform or prepare data before rules are evaluated.

        `pre_processing.source`
        :   Defines the code for the pre-processing logic.
            `entrypoint`: The class and method for pre-processing (e.g., `processing.PreProcessor`).
            `path`: The directory path for the pre-processing code (e.g., `pre_processors/processor`).

        `pre_processing.result_examples_file`
        :   The path to a JSON file containing examples of the data *after* pre-processing and rule execution (if applicable to show final state). The format is an array of objects.

        `pre_processing.pre_result_examples_file`
        :   The path to a JSON file containing examples of the data *before* pre-processing. The format is an array of objects. (I've added this based on the YAML, please clarify if this understanding is correct or if `pre_result_examples_file` had a different purpose.)


### Result Example JSON Format

The `result_example.json` (and assumed `pre_result_example.json`) file should follow this structure:

```json title="result_example.json"
[
    {
        "urn": "<identifier_for_contact>",
        "data": {
            "key1": "value1",
            "key2": "value2"
            // ... other data fields relevant to the example
        }
    },
    {
        "urn": "<another_contact_identifier>",
        "data": {
            "fieldA": "dataA",
            "fieldB": "dataB"
        }
    }
    // ... more examples
]
```
Each object in the array represents a test case or an example scenario.
- `urn`: A unique identifier for the contact (e.g., a phone number, user ID).
- `data`: An object containing the data relevant to this specific example. The structure of this `data` object will depend on your agent's specific needs and the information it processes.

## Basic Structure

The project structure for an Active Agent might look like this, incorporating rules and pre-processing logic:

```
your-project-name/
├── rules/
│   ├── status_aprovado/
│   │   └── main.py
│   │   └── requirements.txt
│   └── status_invoiced/
│       └── main.py
│       └── requirements.txt
├── pre_processors/
│   └── processor/
│       └── processing.py
│       └── requirements.txt
├── agent_definition.yaml
└── result_example.json 
```

This structure helps organize the different components of your Active Agent. 