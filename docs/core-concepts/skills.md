# Skills

## Using Skills in Your Agent

Once you've created a skill, you can register it with your agent and use it in your conversations. The agent will automatically detect when to use the skill based on the context of the conversation.

Skills allow your agent to:
- Fetch data from external APIs
- Perform calculations
- Interact with databases
- Execute custom business logic
- And much more!

By creating custom skills, you can extend your agent's capabilities to handle specific tasks relevant to your use case.

from weni import Skill
from weni.context import Context
from weni.responses import TextResponse
import requests

class GetAddress(Skill):
    def execute(self, context: Context) -> TextResponse:
        
        cep = context.parameters.get("cep", "")

        print(cep)

        address_response = self.get_address_by_cep(cep=cep)

        print(address_response)

        return TextResponse(data=address_response)
    
    def get_address_by_cep(self, cep):
        url = f"https://viacep.com.br/ws/{cep}/json/"
        
        response = requests.get(url)
        
        return response.json()

## Code Explanation

Let's break down this example:

1. **Imports**: We import the necessary classes from the Weni framework and the `requests` library for making HTTP requests.

2. **Class Definition**: We create a class called `GetAddress` that inherits from `Skill`.

3. **Execute Method**: This is the main method that will be called when the skill is triggered.
   - It receives a `context` parameter that contains information about the current conversation
   - It extracts the "cep" parameter from the context
   - It calls the `get_address_by_cep` method to fetch the address information
   - It returns a `TextResponse` with the address data

4. **Helper Method**: The `get_address_by_cep` method makes an HTTP request to the ViaCEP API and returns the JSON response.