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
          path: "path/to/agent_skill_folder"
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
   - Implemented as Lambda functions

## Creating Skills

### Lambda Function Structure

```python
def lambda_handler(event, context):
    # Extract parameters
    parameters = event.get('parameters', [])
    
    # Process the request
    result = process_request(parameters)
    
    # Format response
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event['actionGroup'],
            'function': event['function'],
            'functionResponse': {
                'responseBody': {
                    'TEXT': {'body': result}
                }
            }
        },
        'sessionAttributes': event.get('sessionAttributes', {}),
        'promptSessionAttributes': event.get('promptSessionAttributes', {})
    }
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
- Text responses
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
   - Verify skill entrypoint
   - Test Lambda function locally
   - Check parameter handling
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
