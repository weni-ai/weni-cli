# Quick Start for Developers

This guide is designed for developers who want full control over agent creation and customization with Weni CLI.

## Prerequisites

Before you begin, make sure you have:

1. **Installed Weni CLI**
   - Follow the [installation guide](installation.md)
   - Verify installation with `weni --version`

2. **Created a Weni Account**
   - Sign up at [Weni.ai](https://weni.ai/)
   - Ensure you have access to at least one project

3. **Development Environment**
   - A code editor of your choice
   - Basic understanding of YAML and Python

## Step-by-Step Guide

### 1. Login and Project Setup

1. **Login to Weni**
   ```bash
   weni login
   ```

2. **List Your Projects**
   ```bash
   weni project list
   ```

3. **Select Your Project**
   ```bash
   weni project use your-project-uuid
   ```

4. **Verify Current Project**
   ```bash
   weni project current
   ```

### 2. Use Weni Init

```bash
weni init
```

This command will create a new agent with the name `cep_agent` and the skill `get_address`.

#### 2.1. Agent Configuration

Create a file named `agents.yaml` with your agent configuration:

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

#### 2.2. Skill Implementation

1. **Create Skill Directory**
   ```bash
   mkdir -p skills/cep_agent
   cd skills/cep_agent
   ```

2. **Create Lambda Function**
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

3. **Create Requirements File (Optional)**
   If you are using any external libraries, create a `requirements.txt` file:

   ```txt
   urllib3==2.3.0
   ```

### 3. Deploy Agent

```bash
weni project push agents.yaml
```

## Advanced Configuration

### Custom Parameters

You can add more parameters to your skills:

```yaml
parameters:
  - format:
      description: "Response format (json or text)"
      type: "string"
      required: false
      default: "json"
```

### Multiple Skills

Agents can have multiple skills:

```yaml
skills:
  - get_address:
      # skill definition
  - validate_cep:
      # another skill definition
```

## What's Next?

- Learn about [advanced agent features](../user-guide/agents.md#advanced-topics)
- Explore [skill development best practices](../user-guide/skills.md)
- See [example implementations](../examples/) 