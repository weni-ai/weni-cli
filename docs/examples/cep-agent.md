# CEP Agent Example

This example shows how to create an agent that can provide address information based on Brazilian postal codes (CEP).

## Agent Definition

Create a file named `agents.yaml`:

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
          path: "cep_agent"
          description: "Function to get the address from the postal code"
          parameters:
            - cep:
                description: "postal code of a place"
                type: "string"
                required: true
                custom_field: true
```

## Lambda Function

Create a file `cep_agent/lambda_function.py`:

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

## Deployment Steps

1. Deploy the agent:
   ```bash
   weni project push agents.yaml
   ```

## Testing

After deployment, you can test the agent by:

1. Opening your project in the Weni platform
2. Finding the CEP Agent in your agents list
3. Starting a conversation
4. Sending a valid Brazilian postal code (e.g., "01311-000")
