# Events

## What Are Events?

Events allow your tools to register analytics data that is sent to the Weni Datalake for tracking, reporting, and conversation classification. They are the way tools communicate what happened during execution to the analytics system.

## Why Events Matter

Events enable tools to:

- Track conversation outcomes (resolved, unresolved, transferred)
- Log custom analytics data during tool execution
- Feed data into reports and dashboards
- Provide visibility into what tools are doing in production

## Quick Start

To register an event, call `self.register_event()` inside your tool's `execute` method:

```python
from weni import Tool
from weni.context import Context
from weni.events.event import Event
from weni.responses import TextResponse


class MyTool(Tool):
    def execute(self, context: Context):
        result = do_work()

        self.register_event(Event(
            event_name="order_placed",
            key="order_123",
            value_type="string",
            value="completed",
            metadata={"customer": "John Doe"},
        ))

        return TextResponse(data=result)
```

Events are collected automatically by the framework and returned to Nexus after tool execution.

## Event Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_name` | `str` | Yes | Name of the event (e.g., `"order_placed"`, `"weni_nexus_data"`) |
| `key` | `str` | Yes | Unique key for the event (e.g., `"conversation_classification"`) |
| `value_type` | `str` | Yes | Type of value (`"string"`, `"int"`, etc.) |
| `value` | `Any` | Yes | The event value (e.g., `"resolved"`, `42`) |
| `metadata` | `dict` | No | Additional metadata (default: `{}`) |
| `date` | `str` | No | ISO 8601 date string (default: current time) |

## Registering Multiple Events

You can register multiple events in a single tool execution:

```python
class MyTool(Tool):
    def execute(self, context: Context):
        self.register_event(Event(
            event_name="tool_started",
            key="exec_001",
            value_type="string",
            value="started",
        ))

        result = expensive_operation()

        self.register_event(Event(
            event_name="tool_completed",
            key="exec_001",
            value_type="string",
            value="completed",
            metadata={"duration_ms": 150},
        ))

        return TextResponse(data=result)
```

## Event Payload

Each event is serialized to a dictionary:

```json
{
    "event_name": "order_placed",
    "key": "order_123",
    "date": "2026-03-31T19:45:00.000000",
    "value_type": "string",
    "value": "completed",
    "metadata": {"customer": "John Doe"}
}
```

## Isolation Between Executions

Events are scoped to each tool execution. On AWS Lambda warm starts, events from a previous invocation are never carried over to the next one. Each call to `Tool.__new__()` starts with a clean event registry.

This ensures that if your tool is invoked 100 times in sequence on the same Lambda, each invocation reports only its own events.

## Legacy API (Deprecated)

The static `Event.register()` method still works but is deprecated and will be removed in version 3.0.0:

```python
# Deprecated - still works but emits a warning
Event.register(Event(
    event_name="my_event",
    key="key_001",
    value_type="string",
    value="hello",
))
```

Use `self.register_event()` instead for proper isolation and to avoid deprecation warnings.

## Complete Example

```python
from weni import Tool
from weni.context import Context
from weni.events.event import Event
from weni.responses import TextResponse


class ClassifyConversation(Tool):
    def execute(self, context: Context):
        user_message = context.parameters.get("message", "")
        classification = self.classify(user_message)

        self.register_event(Event(
            event_name="weni_nexus_data",
            key="conversation_classification",
            value_type="string",
            value=classification,
            metadata={
                "contact_urn": context.contact.get("urn", ""),
                "message_preview": user_message[:100],
            },
        ))

        return TextResponse(data={
            "classification": classification,
            "message": user_message,
        })

    def classify(self, message: str) -> str:
        if "help" in message.lower():
            return "unresolved"
        return "resolved"
```

## Best Practices

1. **Use `self.register_event()`**: Always prefer the instance method over the deprecated `Event.register()` for proper execution isolation
2. **Include relevant metadata**: Add context like `contact_urn`, durations, or error details to make events useful for debugging and analytics
3. **Use consistent event names**: Standardize `event_name` and `key` values across your tools for easier querying in the Datalake
4. **Keep values simple**: Use primitive types for `value` (`string`, `int`, `bool`) to ensure compatibility with the Datalake
