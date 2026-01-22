# Constants

Constants are configurable values that can be defined at the agent level and shared across all tools of that agent. They allow you to define reusable configuration values that can be customized when deploying your agent. To fully understand how to incorporate constants into your agents, we recommend reading this entire content and the following complementary resources: [Agents](./agents.md) and [Tools](./tools.md).

Constants are useful for:

- [x] Defining default configuration values for your agent
- [x] Creating reusable settings that can be customized per deployment
- [x] Providing user-configurable options through the Weni Platform interface

## Constant Structure

In your agent definition file (YAML), constants are defined in the `constants` section at the agent level and follow this structure:

```yaml
agents:
  my_agent:
    name: "My Agent"
    description: "Agent description"
    constants:
      API_ENDPOINT:
        label: "API Endpoint"
        type: "text"
        max_length: 255
        required: true
        default: "https://api.example.com"
      ENVIRONMENT:
        label: "Environment"
        type: "select"
        options:
          - label: "Development"
            value: "DEV"
          - label: "Production"
            value: "PROD"
        default: "DEV"
        required: false
      ENABLE_LOGGING:
        label: "Enable Logging"
        type: "radio"
        options:
          - label: "Yes"
            value: "true"
          - label: "No"
            value: "false"
        default: "true"
        required: true
    tools:
      - my_tool:
          name: "My Tool"
          description: "Tool description"
          source:
            path: "tools/my_tool"
            entrypoint: "main.MyTool"
```

## Types of Constants

Constants support different types to accommodate various configuration needs:

### Text Input (`type: "text"`)

Used for text-based configuration values with a maximum length constraint.

**Required attributes:**
- **label**: Human-readable name displayed in the Weni Platform interface
- **type**: Must be `"text"`
- **max_length**: Maximum number of characters allowed (must be greater than 0)
- **required**: Boolean indicating if the constant is mandatory
- **default**: Default value for the constant

**Example:**
```yaml
constants:
  API_URL:
    label: "API URL"
    type: "text"
    max_length: 255
    required: true
    default: "https://api.example.com"
```

### Select/Radio/Checkbox Options

Used for constants that allow selection from predefined options. The `type` field determines how the options will be displayed in the interface.

**Required attributes:**
- **label**: Human-readable name displayed in the Weni Platform interface
- **type**: Must be `"select"`, `"radio"`, or `"checkbox"`
- **options**: Array of available options
  - **label**: Display text for the option
  - **value**: Actual value that will be used
- **required**: Boolean indicating if the constant is mandatory
- **default**: Default value for the constant

**Example:**
```yaml
constants:
  LOG_LEVEL:
    label: "Log Level"
    type: "select"
    options:
      - label: "Debug"
        value: "DEBUG"
      - label: "Info"
        value: "INFO"
      - label: "Warning"
        value: "WARNING"
      - label: "Error"
        value: "ERROR"
    default: "INFO"
    required: true
```

## Constants in Production Environment

When your agent is deployed on the Weni Platform, constants can be configured through the interface, allowing administrators to customize agent behavior without modifying code.

### How to Configure Constants for Production

1. **Define constants in the YAML file**: Specify all necessary constants in the `constants` section of your agent definition file.

2. **Deploy your agent**: When pushing your agent to the Weni Platform using the CLI, the system will automatically detect the constants defined in your YAML file.

3. **Configure values in the interface**: Administrators will be able to customize the constant values through the Weni Platform interface during agent configuration.

4. **Access constants in tools**: Tools can access constants through the `context.constants` object.

> **Note**: When you assign your agent in the Weni Platform, the constants defined in your YAML file will be displayed in the interface for configuration. For example:
> 
> ```yaml
> agents:
>   weather_agent:
>     name: "Weather Agent"
>     description: "Provides weather information"
>     constants:
>       TEMPERATURE_UNIT:
>         label: "Temperature Unit"
>         type: "select"
>         options:
>           - label: "Celsius"
>             value: "C"
>           - label: "Fahrenheit"
>             value: "F"
>         default: "C"
>         required: true
>       MAX_FORECAST_DAYS:
>         label: "Maximum Forecast Days"
>         type: "text"
>         max_length: 2
>         required: true
>         default: "7"
>     instructions:
>       - "You are a weather information assistant that helps users get accurate forecasts"
>       - "Always provide weather forecasts using the temperature unit configured in the agent settings"
>     tools:
>       - get_weather:
>           name: "Get Weather"
>           source:
>             path: "tools/get_weather"
>             entrypoint: "main.GetWeather"
>           description: "Retrieves weather information"
> ```
> 
> After deploying this agent, administrators can configure the temperature unit and maximum forecast days through the Weni Platform interface.

## Using Constants in Tools

Constants defined at the agent level are accessible to all tools through the `context.constants` object. Here's an example of how to use constants in your tool:

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests

class GetWeather(Tool):
    def execute(self, context: Context) -> TextResponse:
        # Access constants from the agent configuration
        temperature_unit = context.constants.get("TEMPERATURE_UNIT", "C")
        max_days = int(context.constants.get("MAX_FORECAST_DAYS", "7"))
        
        # Use the constants in your tool logic
        location = context.parameters.get("location", "")
        weather_data = self.fetch_weather(location, temperature_unit, max_days)
        
        return TextResponse(data=weather_data)
    
    def fetch_weather(self, location, unit, days):
        # Implementation using the constants
        url = f"https://api.weather.com/forecast"
        params = {
            "location": location,
            "unit": unit,
            "days": days
        }
        response = requests.get(url, params=params)
        return response.json()
```

## Constants for Local Testing

During local development and testing, constants can be provided through environment variables or configuration files.

### Configuring Constants for Local Development

For local testing, you can define constants in a `.env` file in the tool's directory, similar to credentials:

```
TEMPERATURE_UNIT=C
MAX_FORECAST_DAYS=7
```

Alternatively, the CLI will use the default values specified in your agent definition file if no local overrides are provided.

## Best Practices

When working with constants:

1. **Use descriptive labels**: Make labels clear and user-friendly for administrators who will configure them
2. **Provide sensible defaults**: Always include default values that work out of the box
3. **Document options clearly**: When using select/radio/checkbox types, ensure option labels are self-explanatory
4. **Validate in your tools**: Always validate constant values in your tool code and handle missing or invalid values gracefully
5. **Keep constants at agent level**: Constants are shared across all tools in an agent, promoting consistency

## Constants vs Credentials

While both constants and credentials are configurable at the agent level, they serve different purposes:

- **Constants**: General configuration values that can be shared and are not sensitive (e.g., API endpoints, feature flags, display preferences)
- **Credentials**: Sensitive authentication information that requires secure storage (e.g., API keys, passwords, tokens)

Use constants for non-sensitive configuration and credentials for any sensitive authentication data. Read more about credentials in the [Credentials](./credentials.md) documentation.

## Validation Rules

When defining constants in your agent definition file, ensure that:

- All constants have a `label` (string)
- All constants have a `type` (must be one of: `"text"`, `"select"`, `"radio"`, `"checkbox"`)
- All constants have a `default` value
- All constants have a `required` field (boolean)
- Text input constants (`type: "text"`) must have `max_length` (integer > 0)
- Option-based constants (`type: "select"`, `"radio"`, or `"checkbox"`) must have an `options` array (not empty)
- Each option must have both `label` and `value` (strings)

The CLI will validate your constant definitions and provide clear error messages if any requirements are not met.

