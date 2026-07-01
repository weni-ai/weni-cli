# Working with Agents

Learn how to create, configure, and deploy AI agents using Weni CLI.

## Agent Definition File

Agents are defined using YAML files. Here's the basic structure:

```yaml
agents:
   agent_id:
      name: "Agent Name"
      description: "Agent Description"
      instructions:
         - "Instruction 1"
         - "Instruction 2"
      guardrails:
         - "Guardrail 1"
      tools:
         - tool_name:
            name: "Tool Name"
            source:
               path: "tools/tool_name"
               entrypoint: "main.ToolClass"
            description: "Tool Description"
            parameters:
               - param_name:
                  description: "Parameter Description"
                  type: "string"
                  required: true
                  contact_field: true
```

### Key Components

1. **Agent ID**
   - Unique identifier for your agent
   - Used internally by the system

2. **Basic Information**
   - `name`: Display name (max 55 characters)
   - `description`: Brief description of the agent's purpose

3. **Instructions**
   - Guide the agent's behavior
   - Minimum 40 characters each
   - Should be clear and specific

4. **Guardrails**
   - Define boundaries and limitations
   - Prevent unwanted behavior

5. **Tools**
   - Custom functionalities
   - Implemented as Python classes using the Weni SDK

### Tool Source Configuration

The `source` field is critical for locating and executing your tool:

```yaml
source:
  path: "tools/tool_name"
  entrypoint: "main.ToolClass"
```

- **path**: Points to the directory containing your tool implementation
  - Example: `tools/get_address` refers to a folder named `get_address` inside a `tools` directory
  - This folder should contain your Python modules and requirements.txt

- **entrypoint**: Specifies which class to use in which file
  - Format: `filename.ClassName`
  - Example: `main.GetAddress` means:
    - Look for a file named `main.py` in the path directory
    - Find a class named `GetAddress` inside that file
    - This class must inherit from the `Tool` class

Your directory structure should look like:
```
project/
├── agents.yaml
└── tools/
    └── get_address/
        ├── main.py             # Contains GetAddress class
        └── requirements.txt    # Dependencies
```

## Creating Tools

### Tool Implementation Structure

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

class ToolName(Tool):
    def execute(self, context: Context) -> TextResponse:
        # Extract parameters
        parameters = context.parameters
        param_value = parameters.get("param_name", "")
        
        # Process the request
        result = self.process_request(param_value)
        
        # Return response
        return TextResponse(data=result)
        
    def process_request(self, param_value):
        # Your business logic here
        return {"key": "value"}
```

#### Important Requirements
- The class **must** inherit from `Tool`
- The class **must** implement the `execute` method
- The class name **must** match the class name in your entrypoint

## Deploying Agents

### Push Command

Deploy your agent using:

```bash
weni project push agents.yaml
```

The command:

1. Validates your YAML
2. Uploads tools
3. Creates/updates the agent

### Elastic APM instrumentation (passive agents only)

For **passive agents** (tools deployed as AWS Lambdas), you can control Elastic APM instrumentation at push time:

| Flag | Behavior |
|------|----------|
| *(none)* | Preserves the current APM state on each tool Lambda |
| `--use-apm` | Enables APM layers and environment variables on all tool Lambdas in the definition |
| `--remove-apm` | Removes APM instrumentation from all tool Lambdas in the definition |

```bash
# Enable APM on tool Lambdas
weni project push agents.yaml --use-apm

# Remove APM from tool Lambdas
weni project push agents.yaml --remove-apm

# Deploy without changing APM state
weni project push agents.yaml
```

**Important:**

- `--use-apm` and `--remove-apm` cannot be used together.
- These flags apply only to **passive agents**. They are ignored for active agent pushes.
- APM affects **all tools** in the agent definition file for that push.

> **Warning — use APM only for observability**
>
> Enable APM only when you need to observe or debug tool Lambda behavior. APM adds layers and environment variables that **increase cold start time and runtime overhead**, which can degrade Lambda performance.
>
> When investigation is complete, **disable APM** so production traffic is not affected:
>
> ```bash
> weni project push agents.yaml --remove-apm
> ```

After a successful push with `--use-apm`, the CLI displays the same warning in the terminal.

### Deployment Best Practices

1. **Version Control**
   - Keep agent definitions in version control
   - Document changes

2. **Testing**
   - Test locally when possible
   - Start with staging environment
   - Verify all tools work

3. **Organization**
   - Use clear file names
   - Keep related files together
   - Document dependencies

## Advanced Topics

### Parameter Types

Available parameter types:
- `string`
- `number`
- `integer`
- `boolean`
- `array`

### Response Formats

Tools can return:
- Text responses via `TextResponse`
- Structured data 
- Error messages

### Error Handling

Your tools should:
1. Validate inputs
2. Handle exceptions gracefully
3. Return meaningful error messages

## Troubleshooting

### Common Issues

1. **Deployment Failures**
   - Check YAML syntax
   - Verify tool paths
   - Confirm project selection

2. **Tool Errors**
   - Verify tool entrypoint (class name)
   - Test tool class locally
   - Check parameter handling in context
   - Verify API endpoints

3. **Agent Behavior**
   - Review instructions
   - Check guardrails
   - Test with various inputs

### Best Practices

1. **Development Flow**
   - Develop locally
   - Test in staging
   - Deploy to production

2. **Monitoring**
   - Keep deployment logs
   - Monitor tool performance
   - Track user interactions

3. **Updates**
   - Plan changes carefully
   - Test updates thoroughly
   - Document modifications
