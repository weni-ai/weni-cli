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
  cep_agent:
    name: "CEP Agent"
    description: "Weni's CEP agent"
    instructions:
      - "You are an expert in providing addresses to the user based on a postal code provided by the user"
      - "The user will send a ZIP code (postal code) and you must provide the address corresponding to this code."
    guardrails:
      - "Don't talk about politics, religion or any other sensitive topic. Keep it neutral."
    skills:
      - get_address:
          name: "Get Address"
          source: 
            path: "skills/get_address"
            entrypoint: "main.GetAddress"
            path_test: "tests.yaml"
          description: "Function to get the address from the postal code"
          parameters:
            - cep:
                description: "postal code of a place"
                type: "string"
                required: true
                contact_field: true
```

### YAML Elements

=== "Agent"

    `Name`

    :   The name of your agent that will be displayed in the Weni Platform.

    `Credentials`

    :   The credentials used in the skills you define for your agent. For more detailed information about this definition, see [Credentials](./credentials.md).

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

    :   The location or path where the skill can be found. It contains three important elements:
        
        - `path`: The directory path where your skill's code is located. This is typically a relative path from the root of your project.
        
        - `entrypoint`: The specific class that will be executed when the skill is called. It follows the format "file_name.ClassName". You can see a practical example of the skill implementation for this entrypoint in the [example](/core-concepts/skills) page, where the GetAddress class from this example is implemented.
        
        - `path_test`: The location of the test file for your skill, which contains test cases to validate the skill's functionality.

    `Description`

    :   Information about the skill, including its purpose and objectives.

    `Parameters`

    :   The parameters or variables used in your agent's skill.
        
        - `description`: A clear explanation of what the parameter is used for and what kind of data it expects.
        
        - `type`: The data type of the parameter (e.g., string, integer, boolean, object).
        
        - `required`: A boolean value (true/false) indicating whether the parameter must be provided for the skill to function properly. If set to true, the agent will ask the user for this information if it's not available before proceeding with the request.
        
        - `contact_field`: Specifies if the parameter should be stored as a contact field in the user's profile for future reference. If set to true, the respective parameter will become information that persists for the user integrated with the Weni Platform. This brings benefits to the user experience because in future interactions, your agent may not need to request this information from the user again. Read more about contact fields in [Contact Fields](./contact-fields.md).

## Basic Structure

The basic structure of your project should consist of your agent definition written in YAML and your agent's skills organized into directories. It is not mandatory to organize your skills in a 'skills' directory, but it is highly recommended as a best practice.

Based on the definition example below:

``` yaml title="agent_definition.yaml"
agents:
  cep_agent:
    name: "CEP Agent"
    description: "Weni's CEP agent"
    instructions:
      - "You are an expert in providing addresses to the user based on a postal code provided by the user"
      - "The user will send a ZIP code (postal code) and you must provide the address corresponding to this code."
    guardrails:
      - "Don't talk about politics, religion or any other sensitive topic. Keep it neutral."
    skills:
      - get_address:
          name: "Get Address"
          source: 
            path: "skills/get_address"
            entrypoint: "main.GetAddress"
            path_test: "tests.yaml"
          description: "Function to get the address from the postal code"
          parameters:
            - cep:
                description: "postal code of a place"
                type: "string"
                required: true
                contact_field: true
```

Your project should have the following structure:
```
your-project-name/
├── skills/
│   ├── get_address/main.py
└── agent_definition.yaml
```