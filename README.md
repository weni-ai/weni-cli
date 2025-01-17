# Weni-CLI

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
    skills:
      - get_address:
          name: "Get Address"
          path: "get_address.zip"
          description: "Function to get the address from the postal code"
          parameters:
            - cep:
                description: "postal code of a place"
                type: "string"
                required: true
```

### 6. Create the Lambda Function for Your Skill
Create a file named `lambda_function.py` (this is the standard name for Lambda functions, but you can use any name) with this content:
```python
import urllib.request

def cep_search(cep):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    url = f'https://viacep.com.br/ws/{cep}/json/'

    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req) as response:
        response_data = response.read().decode('utf-8')

    return response_data


def lambda_handler(event, context):
    agent = event['agent']
    actionGroup = event['actionGroup']
    function = event['function']
    parameters = event.get('parameters', [])

    cep_value = None
    for param in parameters:
        if param['name'] == 'cep':
            cep_value = param['value']
            break

    response_body = {
        'TEXT': {
            'body': f"{cep_search(cep=cep_value)}"
        }
    }
    
    function_response = {
        'actionGroup': actionGroup,
        'function': function,
        'functionResponse': {
            'responseBody': response_body
        }
    }
    
    session_attributes = event.get('sessionAttributes', {})
    prompt_session_attributes = event.get('promptSessionAttributes', {})
    
    action_response = {
        'messageVersion': '1.0', 
        'response': function_response,
        'sessionAttributes': session_attributes,
        'promptSessionAttributes': prompt_session_attributes
    }
        
    return action_response
```

Now, create a ZIP file containing your Lambda function:
```bash
# On Linux/MacOS
zip get_address.zip lambda_function.py

# On Windows (PowerShell)
Compress-Archive -Path lambda_function.py -DestinationPath get_address.zip
```

Make sure the ZIP file name matches the `path` specified in your `agents.yaml` file and that it's in the same directory.

### 7. Upload Your Agent
```bash
weni project push agents.yaml
```

That's it! You've just created your first agent with a custom skill using Weni-CLI. 

The agent will now be able to:
1. Receive a CEP (postal code) from the user
2. Call the ViaCEP API through your Lambda function
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
    skills:
      - get_order_status:
          name: "Get Order Status"                                                            # Maximum of 53 characters
          path: "skills/order_status.zip"
          description: "Function to get the order status"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
      - get_order_details:
          name: "Get Order Details"                                                           # Maximum of 53 characters
          path: "skills/order_details.zip"
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
