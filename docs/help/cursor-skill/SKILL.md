---
name: weni-agents
description: >-
  Build, test, and deploy Weni AI agents using the weni-agents-toolkit and Weni CLI.
  Use when the user asks about creating agent tools, writing agent_definition.yaml,
  using broadcasts, events, FinalResponse, TextResponse, Weni Flows API, weni eval,
  agent evaluation, contact fields, constants, credentials, deploying agents
  with weni project push, VTEX proxy, retail setup, retailsetup API, or VTEX integration.
---

# Weni Agents Development

This skill provides the complete reference for building agents on the Weni platform using `weni-agents-toolkit` and the Weni CLI.

> **Full reference**: For detailed API payloads, all broadcast types, validation rules, and complete examples, read [constitution.md](constitution.md).

## Quick Reference

### Tool Pattern

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse, FinalResponse

class MyTool(Tool):
    def execute(self, context: Context) -> TextResponse:
        param = context.parameters.get("param_name", "default")
        api_key = context.credentials.get("api_key", "")
        endpoint = context.constants.get("API_ENDPOINT", "")
        return TextResponse(data={"result": param})
```

### Context Namespaces

| Namespace | Purpose | Access Pattern |
|-----------|---------|----------------|
| `context.parameters` | Tool-specific params from YAML | `.get("key", default)` |
| `context.credentials` | Secrets (API keys, tokens) | `.get("key", "")` |
| `context.constants` | Non-sensitive config | `.get("KEY", default)` |
| `context.globals` | Global config | `.get("key")` |
| `context.contact` | Contact data (includes `urn`) | `.get("urn", "")` |
| `context.project` | Project info (includes `auth_token`) | `.get("auth_token")` |

### Response Types — Only Two Allowed

| Type | Agent follow-up? | When to use |
|------|-------------------|-------------|
| `TextResponse(data=...)` | Yes | Agent should interpret data and respond |
| `FinalResponse()` | No | Tool handled communication (broadcasts, side effects) |

> **Do NOT use** `AttachmentResponse`, `QuickReplyResponse`, `ListMessageResponse`, `CTAMessageResponse`, `OrderDetailsResponse`, or `LocationResponse`. These are legacy. Use Broadcasts for rich messages.

### Broadcasts

Send messages directly to the contact during execution via `self.send_broadcast()`:

| Type | Import from `weni.broadcasts` |
|------|-------------------------------|
| `Text` | Simple text message |
| `QuickReply` | Tappable quick reply buttons |
| `WhatsAppCatalog` | Product catalog (retailer IDs, channel resolves) |
| `WeniWebChatCatalog` | Rich catalog with full product details |
| `OneClickPayment` | Saved-card one-click WhatsApp payment |
| `PixPayment` | PIX copy-paste code payment |
| `WhatsAppFlows` | WhatsApp Flows interactive screen |

When using broadcasts, return `FinalResponse()` to avoid duplicate messaging.

### Events

```python
from weni.events.event import Event

self.register_event(Event(
    event_name="weni_nexus_data",  # MUST always be this value
    key="order_placed",
    value_type="string",
    value="completed",
    metadata={"order_id": "123"},
))
```

### Flows API Authentication

```python
import requests

auth_token = context.project.get("auth_token")
headers = {
    "Authorization": f"Token {auth_token}",
    "Content-Type": "application/json",
}
response = requests.get(
    "https://flows.weni.ai/api/v2/contacts.json",
    headers=headers,
    params={"urn": "tel:+5511999999999"},
    timeout=10,
)
response.raise_for_status()
```

### Retail Setup API (VTEX Proxy)

Some projects use the Weni Retail Setup proxy (`https://retailsetup.weni.ai/`) to call VTEX APIs without VTEX credentials. Uses `Bearer {auth_token}` (not `Token`).

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/vtex/projects/store-url/` | GET | Get store URL |
| `/vtex/projects/account-identifier/` | GET | Full VTEX account details (trade policies, sites, licenses) |
| `/api/projects/vtex-account` | GET | VTEX account name (used in base URLs) |
| `/vtex/proxy/` | POST | Generic proxy — forwards any VTEX API call |

**Proxy usage** — always POST, set the VTEX method in body:
```python
response = requests.post(
    "https://retailsetup.weni.ai/vtex/proxy/",
    headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
    json={"method": "GET", "path": "/api/oms/pvt/orders/?q="},
    timeout=15,
)
```

> **Always ask the user**: Does this project use Retail Setup proxy or direct VTEX credentials?

### Agent Definition Structure

```yaml
agents:
  agent_key:
    name: "Max 55 chars"
    description: "Capabilities and when to invoke"
    instructions:
      - "Each min 40 chars"
    guardrails:
      - "Each min 40 chars"
    credentials:
      api_key:
        label: "API Key"
        placeholder: "your-api-key"
        is_confidential: true
    constants:
      API_ENDPOINT:
        label: "API Endpoint"
        type: "text"
        max_length: 255
        required: true
        default: "https://api.example.com"
    tools:
      - tool_key:
          name: "Max 40 chars"
          description: "Max 200 chars"
          source:
            path: "tools/tool_folder"
            entrypoint: "main.ToolClassName"
          parameters:
            - param_name:
                description: "Purpose"
                type: "string"
                required: true
```

### Agent Evaluation

```bash
weni eval init                  # Create agent_evaluation.yml
weni eval run                   # Run all tests
weni eval run --filter "test1"  # Run specific tests
weni eval run --verbose         # Detailed reasoning
```

```yaml
tests:
  greeting:
    steps:
      - Send a greeting "Hello!"
    expected_results:
      - Agent responds with a friendly greeting
```

### CLI Workflow

```bash
weni login
weni project list
weni project use <project-uuid>
weni project push agent_definition.yaml
```

### Project Structure

```
project-root/
├── agent_definition.yaml
├── requirements.txt
└── tools/
    └── tool_name/
        ├── main.py
        ├── requirements.txt
        ├── test_definition.yaml
        ├── .env
        └── .globals
```

## Key Rules

1. Only `TextResponse` and `FinalResponse` are valid return types
2. `event_name` MUST always be `"weni_nexus_data"`
3. Use `self.register_event()` (not deprecated `Event.register()`)
4. Use `self.send_broadcast()` + `FinalResponse()` for rich messages
5. Authenticate Flows API with `context.project.get("auth_token")`
6. Agent `name` max 55 chars, tool `name` max 40 chars, tool `description` max 200 chars
7. Instructions and guardrails min 40 chars each
8. Contact field names: `^[a-z][a-z0-9_]*$`, max 36 chars, not reserved

## Detailed Reference

For complete information including:
- Full API endpoint payloads (query params, body fields, examples)
- All broadcast type field tables and code examples
- Retail Setup / VTEX Proxy full response examples and field details
- Validation rules reference
- Manager-Collaborator architecture
- Active agent / rules-based structure
- Constants and credentials configuration
- Error handling patterns
- Deployment checklist

**Read**: [constitution.md](constitution.md)
