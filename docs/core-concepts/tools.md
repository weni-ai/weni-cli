# Tools

## What Are Tools?

Tools are powerful tools available to your agent that enable it to interact with the external environment and the real world. Think of tools as superpowers for your agent - you can create virtually any capability your agent needs by writing Python code that implements your specific business logic!

## Why Tools Matter

Tools transform your agent from a simple conversational interface into a powerful tool that can:

- Fetch real-time data from external APIs
- Perform complex calculations and data processing
- Interact with databases and storage systems
- Execute custom business logic specific to your needs
- Integrate with third-party services and platforms
- Automate tasks and workflows

## Using Tools in Your Agent

Once you've created a tool, you can relate it to your agent by defining it in your agent's YAML configuration file, as demonstrated in the [Agents](./agents.md) documentation page. The agent will automatically detect when to use the tool based on the context of the conversation.

By creating custom tools, you can extend your agent's capabilities to handle specific tasks relevant to your use case, making your agent truly tailored to your business needs.

## Tool Example: Address Lookup

Here's an example of a tool that allows an agent to interact with the real world to precisely obtain information about a postal code (CEP in Brazil):

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests

class GetAddress(Tool):
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
```

## Code Explanation

=== "For Beginners"

    If you're new to programming, here's a simpler explanation of what this code does:

    1. **Imports**: First, we bring in the tools we need:
       - `Tool`: The base class that gives our tool its core functionality
       - `Context`: Holds information about the conversation
       - `TextResponse`: Helps us send text back to the user
       - `requests`: A tool that lets us get information from websites

    2. **Class Definition**: We create a new tool called `GetAddress` that can look up addresses.

    3. **Execute Method**: This is the main part that runs when someone uses the tool:
       - It gets the postal code (CEP) that the user provided
       - It prints the CEP to help with debugging
       - It calls another function to find the address for that CEP
       - It returns the address information to the user

    4. **Helper Method**: The `get_address_by_cep` function:
       - Takes a postal code as input
       - Creates a web address (URL) to look up that postal code
       - Sends a request to a website that knows about addresses
       - Gets back information about the address and returns it

    Think of this tool like a helper that knows how to look up addresses in a phone book when you give it a postal code!

=== "For Experienced Developers"

    For those familiar with Python and API development:

    1. **Imports**: We import the necessary Weni framework classes (`Tool`, `Context`, `TextResponse`) and the `requests` library for HTTP operations.

    2. **Class Definition**: We define a `GetAddress` class that inherits from the base `Tool` class, which provides the framework integration.

    3. **Execute Method**: This is the entry point that the Weni framework calls:
       - It extracts the "cep" parameter from the context object using a get() with a default empty string
       - It includes debug print statements for logging
       - It delegates the actual API call to a separate method for better separation of concerns
       - It returns a `TextResponse` object with the JSON data from the API

    4. **Helper Method**: The `get_address_by_cep` method:
       - Constructs the ViaCEP API endpoint URL with string interpolation
       - Makes a GET request to the external API
       - Returns the parsed JSON response directly
       - Note that this implementation is minimal and lacks error handling for production use

    This implementation follows a simple separation of concerns pattern but could be enhanced with error handling, input validation, response formatting, and proper logging for production use.

## Creating Your Own Tools

To create your own tool:

1. **Define Your Tool Class**: Create a new Python class that inherits from `Tool`
2. **Implement the Execute Method**: Override the `execute(self, context: Context)` method with your business logic
3. **Add Helper Methods**: Separate concerns by breaking down complex logic into helper methods
4. **Implement Error Handling**: Add robust error handling for API calls, data processing, and edge cases
5. **Add Logging**: Include appropriate logging for monitoring and debugging
6. **Write Tests**: Create comprehensive test cases using the test file specified in `path_test`
7. **Configure Your Tool**: Add your tool to your agent's YAML configuration with appropriate parameters and any credentials required by your tool.

## Tools with Credentials

When your tool needs to interact with external services that require authentication, you'll need to use credentials or secrets. The Weni framework provides a secure way to manage these credentials through the `Context` object.

### How to Access Credentials

Credentials are accessed through the `Context` object that is passed to your tool's `execute` method. This ensures that sensitive information is handled securely and isn't hardcoded in your tool's code.

Here's an example of how to modify our `GetAddress` tool to use credentials for an API that requires authentication:

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests

class GetAddressWithAuth(Tool):
    def execute(self, context: Context) -> TextResponse:
        cep = context.parameters.get("cep", "")
        
        api_key = context.credentials.get("api_key")
        
        address_response = self.get_address_by_cep(cep=cep, api_key=api_key)
        
        return TextResponse(data=address_response)
    
    def get_address_by_cep(self, cep, api_key):
        url = f"https://viacep.com.br/ws/{cep}/json/"
        
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        response = requests.get(url, headers=headers)
        
        return response.json()
```

### Configuring Credentials in Your Agent Definition

To make credentials available to your tool, you need to define them in your agent's YAML configuration file. Here's an example:

```yaml
agents:
  cep_agent:
   credentials:
      - api_key:
          - label: "API Key"
          - placeholder: "Api Key"
    name: "CEP Agent"
    description: "Weni's CEP agent"
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
            entrypoint: "main.GetAddressWithAuth"
            path_test: "tests.yaml"
          description: "Function to get the address from the postal code"
          parameters:
            - cep:
                description: "postal code of a place"
                type: "string"
                required: true
                contact_field: true
```

> **Highly Recommended**: For a comprehensive understanding of how credentials work in production environments and local testing, please read the [Credentials](./credentials.md) documentation page. This will help you properly manage sensitive information and understand the different approaches for development and production environments.

### Best Practices for Handling Credentials

When working with credentials in your tools:

1. **Never hardcode credentials** in your tool's code.
2. **Always access credentials through the Context object**.
3. **Use environment variables** for local development and testing.
4. **Implement proper error handling** for cases where credentials might be missing or invalid.

By following these practices, you can create secure tools that interact with authenticated services while keeping sensitive information protected.

## Best Practices for Tools

When creating tools, follow these best practices:

- **Single Responsibility**: Each tool should have a clear, focused purpose
- **Comprehensive Error Handling**: Implement robust error handling for all external calls and edge cases
- **Input Validation**: Validate all input parameters before processing
- **Security Considerations**: Handle sensitive data appropriately and follow security best practices
- **Testability**: Design your tools to be easily testable with both unit and integration tests
- **Version Control**: Use a GitHub repository to version your tools, allowing you to track changes, collaborate with others, and easily roll back to previous versions if needed
