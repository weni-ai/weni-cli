# CEP Agent Example :material-map-marker:

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
          source: 
            path: "skills/get_address"
            entrypoint: "main.GetAddress"
            path_test: "test_definition.yaml"
          description: "Function to get the address from the postal code"
          parameters:
            - cep:
                description: "postal code of a place"
                type: "string"
                required: true
                contact_field: true
```

## Skill Implementation

Create a file `skills/get_address/main.py`:

```python
from weni import Skill
from weni.context import Context
from weni.responses import TextResponse
import requests


class GetAddress(Skill):
    def execute(self, context: Context) -> TextResponse:
        cep = context.parameters.get("cep", "")
        address_response = self.get_address_by_cep(cep=cep)
        return TextResponse(data=address_response)

    def get_address_by_cep(self, cep):
        url = f"https://viacep.com.br/ws/{cep}/json/"
        response = requests.get(url)
        return response.json()
```

Create a file `skills/get_address/requirements.txt`:

```
requests==2.31.0
```

Create a file `skills/get_address/test_definition.yaml`:

```yaml
tests:
    test_1:
        parameters:
            cep: "01311-000"
    test_2:
        parameters:
            cep: "70150-900"
    test_3:
        parameters:
            cep: "20050-090"
```

## Testing the Skill Locally

Before deploying your agent, you can test the skill locally using the `weni run` command. This allows you to verify that your skill works correctly and debug any issues.

To test the CEP Agent skill:

```bash
weni run agents.yaml sample_agent get_address
```

This command will execute the tests defined in the `test_definition.yaml` file and show you the output. You should see the address information for the Brazilian postal codes specified in the test cases.

If you need more detailed logs for debugging, you can add the `-v` flag:

```bash
weni run agents.yaml sample_agent get_address -v
```

The verbose output will show you more details about the execution process, including the API requests and responses, helping you identify and fix any issues with your skill.

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
