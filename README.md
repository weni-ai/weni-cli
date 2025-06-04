# Weni-CLI

Weni CLI is a highly powerful tool for creating customized AI multi-agents. This command-line interface enables developers to build, deploy, and manage sophisticated AI agents with tailored tools and functionalities across various communication channels. With Weni CLI, you can rapidly prototype, develop, and deploy agents that perfectly match your business requirements and use cases.

For comprehensive guidance and detailed documentation, we strongly recommend visiting our official documentation:
[https://weni-ai.github.io/weni-cli/](https://weni-ai.github.io/weni-cli/)

## Overview

A command-line interface (CLI) tool to manage and interact with projects on the Weni platform.

## Requirements

- Python >= 3.12
- Poetry >= 1.8.5

## Installation

### Install via PIP
You can install the CLI directly using pip:
```bash
pip install weni-cli
```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/weni-ai/weni-cli.git
   cd weni-cli
   ```

2. Install dependencies and make the CLI executable:
   ```bash
   poetry shell
   poetry install
   ```

## Quick Start [Step by Step]

After setting up your environment, follow these steps to create your first agent:

### 1. Login to Weni
```bash
weni login
```
This will open your browser for authentication. After successful login, you can close the browser tab.

### 2. List Available Projects
```bash
weni project list
```
This command will show all projects you have access to. Note down the UUID of the project you want to work with.

### 3. Select Your Project
```bash
weni project use your-project-uuid
```
Replace `your-project-uuid` with the UUID from the project list.

### 4. Verify Current Project
```bash
weni project current
```
This ensures you're working with the correct project.

### 5. Create Your Agent Definition
Create a file named `agents.yaml` (you can use any filename you prefer) with this content:
```yaml
agents:
  sample_agent:
    name: "CEP Agent"
    description: "Weni's sample agent"
    instructions:
      - "You are an expert in providing addresses to the user based on a postal code provided by the user"
      - "The user will send a ZIP code (postal code) and you must provide the address corresponding to this code."
    guardrails:
      - "Don't talk about politics, religion or any other sensitive topic. Keep it neutral."
    tools:
      - get_address:
          name: "Get Address"
          source: 
            path: "tools/get_address"
            entrypoint: "main.GetAddress"
          description: "Function to get the address from the postal code"
          parameters:
            - cep:
                description: "postal code of a place"
                type: "string"
                required: true
                contact_field: true
```

### 6. Create Your tool Folder
Create a folder for your tool:
```bash
mkdir -p tools/get_address
```

### 7. Create the tool Class
Create a file in `tools/get_address` named `main.py` with this content:
```python
from weni import tool
from weni.context import Context
from weni.responses import TextResponse
import requests


class GetAddress(tool):
    def execute(self, context: Context) -> TextResponse:
        cep = context.parameters.get("cep", "")
        address_response = self.get_address_by_cep(cep=cep)
        return TextResponse(data=address_response)

    def get_address_by_cep(self, cep):
        url = f"https://viacep.com.br/ws/{cep}/json/"
        response = requests.get(url)
        return response.json()
```

Make sure the file folder matches the `path` specified in your `agents.yaml` file.

### 7.1 Create the requirements.txt file

Create a `requirements.txt` file in the same folder as your tool with the necessary dependencies:

```txt
requests==2.31.0
```

### 8. Upload Your Agent
```bash
weni project push agents.yaml
```

That's it! You've just created your first agent with a custom tool using Weni-CLI. 

The agent will now be able to:
1. Receive a CEP (postal code) from the user
2. Call the ViaCEP API through your tool
3. Return the address information to the user

## Features

- **Login**: Authenticate with Weni to access your projects.
- **List projects**: View a list of all projects available in your account.
- **Select project**: Set the project to be used by the CLI.
- **Current project**: Display information about the currently selected project.
- **Push project definition**: Upload the agents definition file to the selected project.

## Usage

### 1. Login
Log in to your Weni account:
```bash
weni login
```
This will open your default browser for authentication. After successful login, you can close the browser tab.

### 2. List projects
View all projects associated with your account:
```bash
weni project list
```

### 3. Select project
Choose the project you want to work with:
```bash
weni project use <project-uuid>
```
Replace `<project-uuid>` with the UUID of your project from the list command.

### 4. View current project
Check the currently configured project:
```bash
weni project current
```

### 5. Push project definition
Upload a YAML definition file to the configured project:
```bash
weni project push <definition_file.yaml>
```
Replace `<definition_file.yaml>` with the path to your YAML definition file.

## Agent Definition File Structure

Below is an example of a valid agent definition file structure:

```yaml
agents:
  sample_agent:
    name: "Sample Agent"                                                                      # Maximum of 128 characters
    description: "Weni's sample agent"
    instructions:
      - "You should always be polite, respectful and helpful, even if the user is not."       # Minimum of 40 characters
      - "If you don't know the answer, don't lie. Tell the user you don't know."              # Minimum of 40 characters
    guardrails:
      - "Don't talk about politics, religion or any other sensitive topic. Keep it neutral."  # Minimum of 40 characters
    tools:
      - get_order_status:
          name: "Get Order Status"                                                            # Maximum of 53 characters
          source: 
            path: "tools/order_status"
            entrypoint: "main.GetOrderStatus"
          description: "Function to get the order status"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
      - get_order_details:
          name: "Get Order Details"                                                           # Maximum of 53 characters
          source: 
            path: "tools/order_details"
            entrypoint: "main.GetOrderDetails"
          description: "Function to get the order details"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true

## Examples

- Log in and list projects:
  ```bash
  weni login
  weni project list
  ```

- Set and check the current project:
  ```bash
  weni project use 12345678-1234-1234-1234-123456789012
  weni project current
  ```

- Push a definition file:
  ```bash
  weni project push definition.yaml
  ```

## Contributing

Contributions are welcome! Follow the steps below to contribute:

1. Fork the repository.
2. Create a branch for your feature or bug fix:
   ```bash
   git checkout -b my-feature
   ```
3. Commit your changes:
   ```bash
   git commit -m "Description of my feature"
   ```
4. Push your branch:
   ```bash
   git push origin my-feature
   ```
5. Open a Pull Request in the original repository.
