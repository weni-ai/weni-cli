# Quick Start for Developers

This guide is designed for developers who want full control over agent creation and customization with Weni CLI.

## Prerequisites

Before you begin, make sure you have:

1. **Installed Weni CLI**
   - Follow the [installation guide](installation.md)

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

This command will create a new agent with the name `cep_agent` and the tool `get_address`.

#### 2.1. Agent Configuration

Create a file named `agent_definition.yaml` with your agent configuration:

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
```

##### Understanding the Source Configuration

In the YAML above, note the `source` field:

```yaml
source: 
  path: "tools/get_address"
  entrypoint: "main.GetAddress"
```

- **path**: Specifies the directory containing your tool implementation
  - `tools/get_address` means a folder named `get_address` inside a `tools` directory
  - This is where your Python files and requirements.txt should be located

- **entrypoint**: Tells the system which class to use
  - `main.GetAddress` means:
    - Find a file named `main.py` in the path directory
    - Use the `GetAddress` class inside that file
    - The class must inherit from the `Tool` base class

Your project structure should look like:
```
my-agent-project/
├── agent_definition.yaml
└── tools/
    └── get_address/
        ├── main.py             # Contains GetAddress class
        └── requirements.txt    # Dependencies
```

#### 2.2. Tool Implementation

1. **Create Tool Directory**
   ```bash
   mkdir -p tools/get_address
   cd tools/get_address
   ```

2. **Create Tool Class**
   Create a file `tools/get_address/main.py`:

   ```python
   from weni import Tool
   from weni.context import Context
   from weni.responses import TextResponse
   import requests


   class GetAddress(Tool):
       def execute(self, context: Context) -> TextResponse:
           cep = context.parameters.get("cep", "")
           address_response = self.get_address_by_cep(cep=cep)
           return TextResponse(data=address_response)

       def get_address_by_cep(self, cep):
           url = f"https://viacep.com.br/ws/{cep}/json/"
           response = requests.get(url)
           return response.json()
   ```

   **Important**: 
   - The class name `GetAddress` must match the class name in your entrypoint
   - The file name `main.py` must match the file name in your entrypoint
   - The class must inherit from `Tool` and implement the `execute` method

3. **Create Requirements File**
   Create a `requirements.txt` file:

   ```txt
   requests==2.32.3
   ```

4. **(Optional) Add credentials and globals files**

Place these files in `tools/get_address/` if needed during local runs:

```ini
# .env
api_key=your-development-api-key
```

```ini
# .globals
BASE_URL=https://api.example.com
```

### 3. Deploy Agent

```bash
weni project push agent_definition.yaml
```

## Advanced Configuration

### Custom Parameters

You can add more parameters to your tools:

```yaml
parameters:
  - format:
      description: "Response format (json or text)"
      type: "string"
      required: false
      default: "json"
```

### Multiple Tools

Agents can have multiple tools:

```yaml
tools:
  - get_address:
      # tool definition
  - validate_cep:
      # another tool definition
```