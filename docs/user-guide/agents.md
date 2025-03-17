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
    skills:
      - skill_name:
          name: "Skill Name"
          source:
            path: "skills/skill_name"
            entrypoint: "main.SkillClass"
          description: "Skill Description"
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
   - `name`: Display name (max 128 characters)
   - `description`: Brief description of the agent's purpose

3. **Instructions**
   - Guide the agent's behavior
   - Minimum 40 characters each
   - Should be clear and specific

4. **Guardrails**
   - Define boundaries and limitations
   - Prevent unwanted behavior

5. **Skills**
   - Custom functionalities
   - Implemented as Python classes using the Weni SDK

## Creating Skills

### Skill Implementation Structure

```python
from weni import Skill
from weni.context import Context
from weni.responses import TextResponse

class SkillName(Skill):
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

## Deploying Agents

### Push Command

Deploy your agent using:

```bash
weni project push agents.yaml
```

The command:
1. Validates your YAML
2. Uploads skills
3. Creates/updates the agent

### Deployment Best Practices

1. **Version Control**
   - Keep agent definitions in version control
   - Document changes

2. **Testing**
   - Test locally when possible
   - Start with staging environment
   - Verify all skills work

3. **Organization**
   - Use clear file names
   - Keep related files together
   - Document dependencies

## Advanced Topics

### Parameter Types

Available parameter types:
- `string`
- `number`
- `boolean`
- `array`
- `object`

### Response Formats

Skills can return:
- Text responses via `TextResponse`
- Structured data 
- Error messages

### Error Handling

Your skills should:
1. Validate inputs
2. Handle exceptions gracefully
3. Return meaningful error messages

## Troubleshooting

### Common Issues

1. **Deployment Failures**
   - Check YAML syntax
   - Verify skill paths
   - Confirm project selection

2. **Skill Errors**
   - Verify skill entrypoint (class name)
   - Test skill class locally
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
   - Monitor skill performance
   - Track user interactions

3. **Updates**
   - Plan changes carefully
   - Test updates thoroughly
   - Document modifications
