# FinalResponse

## Overview

`FinalResponse` is a special response type that tells the agent that your tool has **fully handled the interaction**. When a tool returns `FinalResponse()`, the agent stops — it will not generate or send any additional message to the contact after the tool finishes.

This is the key difference from `TextResponse`, where the agent receives the returned data and may compose a follow-up message to the contact based on it.

## Why FinalResponse Matters

By default, when a tool returns `TextResponse(data=...)`, the agent uses the returned data to generate a message to the user. This works well when the tool fetches information and the agent should interpret it and respond naturally.

However, there are scenarios where the tool itself already communicates with the user — for example, by sending a broadcast message, a product catalog, or an interactive quick reply. In these cases, having the agent send an additional message would be redundant or confusing. `FinalResponse` prevents this by telling the agent to stop.

## Quick Start

```python
from weni import Tool
from weni.context import Context
from weni.responses import FinalResponse

class MyTool(Tool):
    def execute(self, context: Context) -> FinalResponse:
        # Tool handles the interaction directly
        return FinalResponse()
```

## FinalResponse vs TextResponse

| Return Type | Agent sends a follow-up message? | When to use |
|-------------|----------------------------------|-------------|
| `FinalResponse()` | No — the agent stops, no further message is sent | The tool already handled the user-facing communication |
| `TextResponse(data=...)` | Yes — the agent may generate a message based on the returned data | You want the agent to interpret the tool result and respond to the user |

## When to Use FinalResponse

### With Broadcasts

The most common use case for `FinalResponse` is when your tool sends messages to the contact via [broadcasts](./broadcasts.md). Since the broadcast already delivers the content to the user, the agent doesn't need to send anything else.

```python
from weni import Tool
from weni.context import Context
from weni.responses import FinalResponse
from weni.broadcasts import Text, QuickReply

class NotifyUser(Tool):
    def execute(self, context: Context) -> FinalResponse:
        self.send_broadcast(Text(text="Your order has been confirmed!"))
        self.send_broadcast(QuickReply(
            text="What would you like to do next?",
            options=["Track Order", "Continue Shopping"],
        ))
        return FinalResponse()
```

### With Catalog Messages

When sending product catalogs via broadcast, always use `FinalResponse` to avoid the agent sending a redundant text message on top of the catalog.

```python
from weni import Tool
from weni.context import Context
from weni.responses import FinalResponse
from weni.broadcasts import WhatsAppCatalog, WhatsAppProductGroup

class SendCatalog(Tool):
    def execute(self, context: Context) -> FinalResponse:
        self.send_broadcast(WhatsAppCatalog(
            text="Here are our products:",
            products=[
                WhatsAppProductGroup(
                    product="Featured",
                    product_retailer_ids=["12552#1#1", "12553#1#1"],
                ),
            ],
        ))
        return FinalResponse()
```

### Side-Effect-Only Tools

`FinalResponse` is also useful for tools that perform side effects (e.g., updating a database, triggering a webhook) where no response to the user is needed.

```python
class UpdatePreferences(Tool):
    def execute(self, context: Context) -> FinalResponse:
        language = context.parameters.get("language")
        self.save_user_preference("language", language)
        return FinalResponse()

    def save_user_preference(self, key, value):
        # Persist the preference
        ...
```

## Best Practices

1. **Use `FinalResponse` when your tool already talks to the user**: If you send broadcasts, catalogs, or any interactive message, return `FinalResponse()` to prevent duplicate messages
2. **Use `TextResponse` when the agent should respond**: If the tool fetches data that the agent needs to interpret and present, return `TextResponse(data=...)` instead
3. **Don't mix both intentions**: If you send a broadcast and also return `TextResponse`, the user may receive both the broadcast and an agent-generated message — which is usually not the desired behavior
