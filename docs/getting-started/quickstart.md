# Quick Start Guide

This guide will help you get started with Weni CLI by creating your first agent. We'll create a simple CEP (Brazilian postal code) agent that can provide addresses based on postal codes.

## Prerequisites

1. [Install Weni CLI](installation.md)
2. Have a Weni account (staging or production)

## Step-by-Step Guide

### 1. Login to Weni

```bash
weni login
```

This will open your browser for authentication. After successful login, you can close the browser tab.

### 2. List Your Projects

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

### 5. Create Agent Definition

Create a file named `agents.yaml`:

#### Note that the `path` field in the `skills` section should point to the folder where the Lambda function for that skill is located.

```yaml
agents:
  sample_agent:
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
            path: "skills/cep_agent"
            entrypoint: "lambda_function.lambda_handler"
          description: "Function to get the address from the postal code"
          parameters:
            - cep:
                description: "postal code of a place"
                type: "string"
                required: true
```

### 6. Create Agent skill folder

Create a folder named `skills/cep_agent`:

```bash
mkdir skills
mkdir skills/cep_agent
cd skills/cep_agent
```

### 7. Create Lambda Function inside skills/cep_agent folder

Create a file `skills/cep_agent/lambda_function.py`:

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
    parameters = event.get('parameters', [])
    cep_value = next((param['value'] for param in parameters 
                     if param['name'] == 'cep'), None)
    
    response_body = {'TEXT': {'body': cep_search(cep=cep_value)}}
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event['actionGroup'],
            'function': event['function'],
            'functionResponse': {'responseBody': response_body}
        },
        'sessionAttributes': event.get('sessionAttributes', {}),
        'promptSessionAttributes': event.get('promptSessionAttributes', {})
    }
```

### 7.1. Create the requirements.txt file (optional)

If you are using any external libraries, you must create a `requirements.txt` file with the dependencies versions:

Example:
```txt
urllib3==2.3.0
```

### 8. Deploy Agent

```bash
weni project push agents.yaml
```

## What's Next?

- Learn more about [agent configuration](../user-guide/agents.md)
- Explore [project management](../user-guide/projects.md)
- See more [examples](../examples/cep-agent.md)
