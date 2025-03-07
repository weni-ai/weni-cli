# Agents

## Overview

Agents are AI-powered workers designed to operate autonomously within specific contexts, using generative AI to make decisions based on given problems. In the context of Weni CLI, agents are specifically optimized for customer service operations, serving as the frontline communication interface between companies and their customers.

Key features:

- [x] Autonomous decision-making capabilities
- [x] Context-specific operations
- [x] Built-in generative AI processing
- [x] Customer service optimization

With Weni CLI, you can define and deploy multiple agents that work together to solve real-world problems with precision, quality, and security. These agents can be equipped with various skills that enable them to interact with the external world within defined boundaries.

## Creating an Agent

An agent consists of an agent definition. In Weni CLI, this definition is made using a YAML file, where you can write your agent however you want.

Here is an example of how you can define your agent in a YAML file:

``` yaml title="agent_definition.yaml"
agents:
  sample_agent:
    name: "Sample Agent"
    description: "Weni's sample agent"
    instructions:
      - "You should always be polite, respectful and helpful, even if the user is not."
      - "If you don't know the answer, don't lie. Tell the user you don't know."
    guardrails:
      - "Don't talk about politics, religion or any other sensitive topic. Keep it neutral."
    skills:
      - get_order_status:
          name: "Get Order Status"
          source: 
            path: "skills/order_status"
            entrypoint: "lambda_function.lambda_handler"
          description: "Function to get the order status"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
      - get_order_details:
          name: "Get Order Details"                                                           
          source: 
            path: "skills/order_details"
            entrypoint: "lambda_function.lambda_handler"
          description: "Function to get the order details"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
```

### YAML Elements

=== "Agent"

    `Name`

    :   The name of your agent that will be displayed in the Weni Platform.

    `Credentials`

    :   The credentials used in the skills you define for your agent.

    `Description`

    :   Important information about your agent, where you can describe its purpose, capabilities, and other relevant details.

    `Instructions`

    :   Here you can define rules and guidelines that your agent should follow.

    `Guardrails`

    :   You can list boundaries and limitations for your agent, such as topics it should not discuss.

=== "Skill"

    `Name`

    :   The name of the skill that will be associated with the agent in the Weni Platform.

    `Source`

    :   The location or path where the skill can be found.

    `Description`

    :   Information about the skill, including its purpose and objectives.

    `Parameters`

    :   The parameters or variables used in your agent's skill.



## Basic Structure

The basic structure of your project should consist of your agent definition written in YAML and your agent's skills organized into directories. It is not mandatory to organize your skills in a 'skills' directory, but it is highly recommended as a best practice.

Based on the definition example below:

``` yaml title="agent_definition.yaml"
agents:
  sample_agent:
    name: "Sample Agent"
    description: "Weni's sample agent"
    instructions:
      - "You should always be polite, respectful and helpful, even if the user is not."
      - "If you don't know the answer, don't lie. Tell the user you don't know."
    guardrails:
      - "Don't talk about politics, religion or any other sensitive topic. Keep it neutral."
    skills:
      - get_order_status:
          name: "Get Order Status"
          source: 
            path: "skills/order_status"
            entrypoint: "lambda_function.lambda_handler"
          description: "Function to get the order status"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
      - get_order_details:
          name: "Get Order Details"                                                           
          source: 
            path: "skills/order_details"
            entrypoint: "lambda_function.lambda_handler"
          description: "Function to get the order details"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
```

Your project should have the following structure:
```
your-project-name/
├── skills/
│   ├── get_orders_status/
│   ├── get_order_details/
└── agent_definition.yaml
```