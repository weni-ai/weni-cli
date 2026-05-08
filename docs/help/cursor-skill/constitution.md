<!--
  SYNC IMPACT REPORT
  ==================
  Version change: 1.4.0 → 1.5.0
  Modified principles:
    - III. Response Type Discipline → restricted to TextResponse and FinalResponse only;
      legacy types (AttachmentResponse, QuickReplyResponse, ListMessageResponse,
      CTAMessageResponse, OrderDetailsResponse, LocationResponse) marked as unsupported
  Added sections:
    - Agent Evaluation (weni eval init/run, agent_evaluation.yml structure, test writing patterns)
    - Weni Retail Setup API / VTEX Proxy (store-url, account-identifier, vtex-account, proxy)
  Changed sections:
    - Weni Flows API Integration → expanded Available API Endpoints with full
      query-parameter and body-field payloads for every endpoint from the API Explorer
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ (no changes needed)
    - .specify/templates/spec-template.md ✅ (no changes needed)
    - .specify/templates/tasks-template.md ✅ (no changes needed)
  Follow-up TODOs: None
-->

# Weni Agents Constitution

## Core Principles

### I. Tool-First Architecture

All agent capabilities MUST be implemented as Tools using the `weni-agents-toolkit` library. Tools are the building blocks of agent functionality.

**Non-negotiables**:
- Every tool MUST extend the `Tool` base class from `weni`
- Every tool MUST implement the `execute(self, context: Context)` method
- Every tool MUST return a valid Response type (`TextResponse` or `FinalResponse`)
- Tools MUST be stateless—all state comes from the `Context` object
- Tools MUST be independently testable via `test_definition.yaml`
- Tools MAY send proactive messages to the contact via `self.send_broadcast()` (see Broadcasts section)
- Tools MAY register analytics events via `self.register_event()` (see Events section)

### II. Context-Driven Execution

Tools receive all required data through the immutable `Context` object. Never rely on external state or global variables.

**Context Namespaces**:
- `context.parameters`: Tool-specific parameters defined in `agent_definition.yaml`
- `context.credentials`: Configured secrets and API keys
- `context.constants`: Agent-level configuration values (non-sensitive)
- `context.globals`: Global configuration values
- `context.contact`: Contact/user data from the conversation (includes `urn`)
- `context.project`: Project-level information (includes `auth_token` for Weni API access)

**Non-negotiables**:
- MUST access parameters via `context.parameters.get("param_name", default_value)`
- MUST NOT modify context data (it is immutable)
- MUST handle missing parameters gracefully with default values
- MUST access credentials via `context.credentials` for sensitive data (API keys, tokens)
- MUST access constants via `context.constants` for non-sensitive configuration values
- MUST access the Weni auth token via `context.project.get("auth_token")` when calling Weni Flows APIs

### III. Response Type Discipline

Tools MUST return appropriate Response types based on the intended user interaction. Never return raw data.

**Available Response Types** (from `weni.responses`):
- `TextResponse(data)`: Simple text messages — the agent receives the data and MAY compose a follow-up message to the contact
- `FinalResponse()`: Signals the tool fully handled the interaction — the agent stops and does NOT send any follow-up message

> **Important**: Only `TextResponse` and `FinalResponse` are supported. Do NOT use `AttachmentResponse`, `QuickReplyResponse`, `ListMessageResponse`, `CTAMessageResponse`, `OrderDetailsResponse`, or `LocationResponse` — these are legacy types and must not be used. For rich interactive messages (buttons, lists, catalogs, etc.), use Broadcasts instead (see Broadcasts section).

**TextResponse vs FinalResponse**:

| Return Type | Agent sends follow-up? | When to use |
|-------------|------------------------|-------------|
| `TextResponse(data=...)` | Yes — agent may generate a message based on data | The agent should interpret results and respond to the user |
| `FinalResponse()` | No — agent stops immediately | The tool already handled user-facing communication (broadcasts, side effects) |

**Non-negotiables**:
- MUST use `TextResponse` when the agent should interpret data and respond
- MUST use `FinalResponse` when the tool sends broadcasts and does not want agent-generated follow-up
- MUST use `FinalResponse` for side-effect-only tools (DB updates, webhooks with no user response)
- MUST NOT return `TextResponse` when also sending broadcasts unless duplicate messaging is intentional
- MUST NOT create custom response classes
- MUST include `data` parameter with the tool's execution result (except for `FinalResponse`)
- Response `data` MUST be JSON-serializable (dict, list, or primitive types)

### IV. Agent Definition Compliance

All agents MUST be defined in `agent_definition.yaml` following the exact YAML schema from Weni CLI. Validation failures will block deployment.

**Required Agent Fields**:
- `name`: String, **maximum 55 characters**
- `description`: String, required (see Description Best Practices below)
- `tools`: Array of tool definitions, required (at least one tool)

**Optional Agent Fields**:
- `instructions`: Array of strings, each **minimum 40 characters**
- `guardrails`: Array of strings, each **minimum 40 characters**
- `credentials`: Object defining secrets (see Credentials Configuration)
- `constants`: Object defining non-sensitive configuration (see Constants Configuration)
- `components`: Array of component definitions

**Description Best Practices** (critical for Manager orchestration):
- MUST clearly describe the agent's capabilities and when it should be invoked
- MUST be concise—the Manager uses this as the sole context for routing decisions
- SHOULD include the primary use cases or triggers for this agent
- SHOULD NOT exceed 2-3 sentences (avoid overly verbose descriptions)
- MUST NOT include implementation details or technical jargon

**Required Tool Fields**:
- `name`: String, **maximum 40 characters**
- `description`: String, **maximum 200 characters**
- `source`: Object with `path` and `entrypoint` (both required strings)
- `source.path`: Relative path to tool folder (e.g., `tools/my_tool`)
- `source.entrypoint`: Module and class name (e.g., `main.MyTool`)

**Optional Tool Fields**:
- `source.path_test`: String, path to test file (default: `test_definition.yaml`)
- `parameters`: Array of parameter definitions

**Parameter Definition**:
- `description`: String, required
- `type`: String, required, one of: `string`, `number`, `integer`, `boolean`, `array`
- `required`: Boolean, optional (default: false)
- `contact_field`: Boolean, optional (see Contact Field Constraints)

### V. Clean Code & Python Standards

All code MUST follow Python best practices and be self-documenting through expressive naming.

**Non-negotiables**:
- Follow [PEP 8](https://peps.python.org/pep-0008/) for formatting, naming, and layout
- Use `snake_case` for functions, variables, modules; `PascalCase` for classes
- Group imports: (1) standard library, (2) third-party, (3) weni toolkit, (4) local
- Use type annotations for all function signatures
- Keep functions with a single responsibility
- Prefer explicit over implicit, simple over complex

**Import Order Example**:
```python
# Standard library
import json
from datetime import datetime

# Third-party
import requests

# Weni toolkit
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse, FinalResponse
from weni.broadcasts import Text, QuickReply
from weni.events.event import Event

# Local
from .helpers import format_data
```

## Manager-Collaborator Architecture

### Overview

Agents created via Weni CLI operate within a **Manager-Collaborator** orchestration model. Understanding this architecture is essential for designing effective agents.

**Architecture Components**:
- **Manager Agent**: The central orchestrator that receives user messages and routes them to appropriate collaborator agents. The Manager is configured exclusively through the Weni UI—it cannot be modified via CLI.
- **Collaborator Agents**: Specialized agents created and deployed via Weni CLI. Each collaborator handles specific domains or capabilities.

### How Routing Works

The Manager decides which collaborator to invoke based on **two pieces of information only**:
1. **Agent Name**: The display name of the collaborator
2. **Agent Description**: The description field serves as **collaboration instructions** for the Manager

**Critical Implication**: The Manager has no visibility into:
- The agent's instructions or guardrails
- The tools available to the agent
- The internal implementation details

This means the **description field is the single most important factor** in ensuring proper task routing.

### Description Guidelines

Since the Manager relies solely on the description to understand what a collaborator can do, follow these guidelines:

**DO**:
- State the primary capability clearly: "Handles order status inquiries and tracking updates"
- Include trigger scenarios: "Use when customer asks about shipping, delivery, or order status"
- Be specific about the domain: "Manages product catalog searches and inventory queries"

**DON'T**:
- Write vague descriptions: "Helps with customer requests" (too generic)
- Include technical details: "Uses REST API to fetch data from backend" (irrelevant to Manager)
- Make descriptions too long: The Manager processes many collaborators; brevity aids routing
- Overlap with other collaborators: Distinct descriptions prevent routing ambiguity

**Example - Good Description**:
```yaml
description: "Retrieves order status, tracking information, and estimated delivery dates. Use when customers ask about their orders, shipments, or delivery times."
```

**Example - Poor Description**:
```yaml
description: "This agent helps customers with various order-related tasks and queries using our internal systems."
```

### Multi-Agent Design Considerations

When designing multiple collaborator agents:

1. **Clear Domain Boundaries**: Each collaborator SHOULD own a distinct domain (orders, products, support, etc.)
2. **Non-Overlapping Descriptions**: Avoid descriptions that could match the same user intent
3. **Complementary Capabilities**: Design collaborators to work together without duplicating functionality
4. **Fallback Strategy**: Consider having a general-purpose collaborator for queries that don't match specialized agents

## Broadcasts

Broadcasts allow tools to send messages directly to the contact **during** execution, before the tool returns its response. They are essential for long-running operations, rich interactive messages, and scenarios where the tool itself should drive the conversation.

### Broadcast Usage Pattern

Call `self.send_broadcast()` inside the tool's `execute` method:

```python
from weni import Tool
from weni.context import Context
from weni.broadcasts import Text
from weni.responses import FinalResponse

class MyTool(Tool):
    def execute(self, context: Context) -> FinalResponse:
        self.send_broadcast(Text(text="Processing your request..."))
        return FinalResponse()
```

**Non-negotiables**:
- MUST call `self.send_broadcast()` inside the `execute()` method (not outside the tool class)
- MUST return `FinalResponse()` when the broadcast IS the primary output (avoids duplicate messaging)
- MAY call `self.send_broadcast()` multiple times in a single execution
- MUST use dict shorthand for nested objects (catalogs, payments) to keep imports minimal

### Broadcast Message Types (`weni.broadcasts`)

| Type | Purpose |
|------|---------|
| `Text` | Simple text message |
| `QuickReply` | Message with tappable quick reply buttons |
| `WhatsAppCatalog` | Lightweight product catalog (retailer IDs only; channel resolves details) |
| `WeniWebChatCatalog` | Rich product catalog with full product details (name, price, image) |
| `OneClickPayment` | Order confirmation with saved card for one-click WhatsApp payment |
| `PixPayment` | Order details with PIX copy-paste code for payment |
| `WhatsAppFlows` | WhatsApp Flows interactive message opening a structured screen |

### Text

```python
from weni.broadcasts import Text

self.send_broadcast(Text(text="Hello! How can I help you?"))
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | ✅ | Message text content |

### QuickReply

```python
from weni.broadcasts import QuickReply

self.send_broadcast(QuickReply(
    text="Do you want to continue?",
    options=["Yes", "No", "Maybe"],
    header="Question",
    footer="Tap to select",
))
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | ✅ | Message text |
| `options` | `list[str]` | ❌ | Quick reply button labels |
| `header` | `str` | ❌ | Optional header text |
| `footer` | `str` | ❌ | Optional footer text |

### WhatsAppCatalog

Use when the channel natively resolves product details from retailer IDs (e.g., WhatsApp Business catalog).

```python
from weni.broadcasts import WhatsAppCatalog

self.send_broadcast(WhatsAppCatalog(
    text="Here are our shirts",
    products=[
        {"product": "Workshirt Titan Coyote", "product_retailer_ids": ["12552#1#1", "12553#1#1"]},
    ],
    header="Our Store",
    footer="Tap a product to view details",
))
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | ✅ | Body text displayed with the catalog |
| `products` | `list[dict]` | ❌ | List of product groups |
| `action_button_text` | `str` | ❌ | Label for action button (default: `"Comprar"`) |
| `send_catalog` | `bool` | ❌ | Whether to send the full catalog (default: `False`) |
| `header` | `str` | ❌ | Optional header text |
| `footer` | `str` | ❌ | Optional footer text |

**Product group dict fields**:
- `product` (str, required): Product group/category name
- `product_retailer_ids` (list[str], required): List of retailer ID strings

### WeniWebChatCatalog

Use when the channel does NOT natively resolve product details (provide full product info inline).

```python
from weni.broadcasts import WeniWebChatCatalog

self.send_broadcast(WeniWebChatCatalog(
    text="Here are our products",
    products=[{
        "product": "Shirts",
        "product_retailer_info": [
            {
                "name": "Blue Shirt",
                "price": "149.90",
                "retailer_id": "85961",
                "seller_id": "1",
                "description": "Premium cotton blue shirt",
                "image": "https://example.com/images/blue-shirt.jpg",
                "product_url": "https://store.com/blue-shirt",
            },
        ],
    }],
    header="Our Store",
    footer="Tap a product to view details",
    action_button_text="Buy Now",
))
```

**Product dict fields** (for `product_retailer_info`):
- `name` (str, required), `price` (str, required), `retailer_id` (str, required), `seller_id` (str, required)
- `currency` (str, optional, default `"BRL"`)
- `description` (str, optional), `image` (str, optional), `sale_price` (str, optional)

### OneClickPayment

```python
from weni.broadcasts import OneClickPayment

self.send_broadcast(OneClickPayment(
    text="We found a saved card. Use it to complete payment?",
    reference_id="ORDER-123",
    last_four_digits="4242",
    credential_id="acc_001",
    total_amount=15000,  # in cents
    items=[
        {"retailer_id": "SKU-1", "name": "Shirt", "amount": 10000, "quantity": 1},
    ],
    subtotal=15000,
    tax_value=500,
    discount_value=1000,
    shipping_value=800,
))
```

**All monetary values are in cents (int)**. Required: `text`, `reference_id`, `last_four_digits`, `credential_id`, `total_amount`.

### PixPayment

```python
from weni.broadcasts import PixPayment

self.send_broadcast(PixPayment(
    text="Copy the PIX code below to complete payment.",
    reference_id="1484830849478-01",
    pix_key="7d4e8f2a-3b1c-4d5e-9f6a-8b7c2d1e0f3a",
    pix_key_type="EVP",  # EVP, CPF, CNPJ, etc.
    merchant_name="CITEROL LTDA",
    pix_code="00020126580014br.gov.bcb.pix...",
    total_amount=34990,  # in cents
    items=[
        {"retailer_id": "31245#1", "name": "Nike Air Max 90", "amount": 24990},
    ],
    subtotal=29990,
    discount_value=1500,
    shipping_value=6500,
    footer="Obrigado pela preferencia",
))
```

**All monetary values are in cents (int)**. Required: `text`, `reference_id`, `pix_key`, `pix_key_type`, `merchant_name`, `pix_code`, `total_amount`.

### WhatsAppFlows

```python
from weni.broadcasts import WhatsAppFlows

self.send_broadcast(WhatsAppFlows(
    text="You have a pending confirmation.",
    flow_id="1451561746318256",
    flow_cta="Confirm Now",
    flow_screen="COLLECT_DATA",
    flow_data={"order_value": "R$ 150,00", "card_last_four": "1234"},
    flow_token="optional-token-123",
))
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | `str` | ✅ | Message text displayed to the contact |
| `flow_id` | `str` | ✅ | WhatsApp Flow ID |
| `flow_cta` | `str` | ✅ | Call-to-action button text |
| `flow_screen` | `str` | ✅ | Initial screen to display |
| `flow_token` | `str` | ❌ | Optional flow token |
| `flow_data` | `dict` | ❌ | Data to pass to the flow (default: `{}`) |
| `flow_mode` | `str` | ❌ | `"published"` or `"draft"` (default: `"published"`) |

### Dict Shorthand

All nested objects support dict shorthand — avoid importing auxiliary classes:

```python
# Preferred — no extra imports
from weni.broadcasts import OneClickPayment

self.send_broadcast(OneClickPayment(
    ...,
    items=[{"retailer_id": "SKU-1", "name": "Shirt", "amount": 15000}],
))
```

### Channel Detection

Detect the channel from the contact URN to pick the right broadcast type:

```python
contact_urn = context.contact.get("urn", "")

if contact_urn.startswith("whatsapp:"):
    self.send_broadcast(WhatsAppCatalog(...))
else:
    self.send_broadcast(WeniWebChatCatalog(...))
```

### Best Practices

1. Use broadcasts for real-time progress feedback on long-running operations
2. Pick the correct catalog type based on channel capabilities
3. Return `FinalResponse()` when the broadcast IS the user-facing output
4. Keep broadcasts concise — avoid flooding the user
5. Always prefer dict shorthand over importing nested helper classes

## FinalResponse

`FinalResponse` is a special response type signaling that the tool has fully handled the interaction — the agent stops immediately and sends no follow-up message.

### When to Use FinalResponse

**Scenario 1: With Broadcasts**
The tool already delivered the content via broadcast; no agent follow-up needed.

```python
class NotifyUser(Tool):
    def execute(self, context: Context) -> FinalResponse:
        self.send_broadcast(Text(text="Your order has been confirmed!"))
        self.send_broadcast(QuickReply(
            text="What would you like to do next?",
            options=["Track Order", "Continue Shopping"],
        ))
        return FinalResponse()
```

**Scenario 2: With Catalogs**
Avoid redundant text on top of a catalog broadcast.

```python
class SendCatalog(Tool):
    def execute(self, context: Context) -> FinalResponse:
        self.send_broadcast(WhatsAppCatalog(
            text="Here are our products:",
            products=[{"product": "Featured", "product_retailer_ids": ["12552#1#1"]}],
        ))
        return FinalResponse()
```

**Scenario 3: Side-Effect-Only Tools**
Tools that update state without needing to respond to the user.

```python
class UpdatePreferences(Tool):
    def execute(self, context: Context) -> FinalResponse:
        language = context.parameters.get("language")
        self.save_user_preference("language", language)
        return FinalResponse()
```

### When NOT to Use FinalResponse

Use `TextResponse(data=...)` instead when:
- The tool fetches data that the agent should interpret and present
- The user expects a natural language response composed by the agent
- Example: fetching order status, looking up addresses, getting weather

**Non-negotiables**:
- MUST NOT mix `self.send_broadcast()` with `TextResponse()` unless duplicate messaging is intentional
- MUST return `FinalResponse()` for pure side-effect tools to prevent empty agent follow-ups
- MUST use `TextResponse(data=...)` when the tool's value is the data itself

## Events

Events register analytics data sent to the Weni Datalake for tracking, reporting, and conversation classification.

### Event Registration Pattern

Use the instance method `self.register_event()` (recommended):

```python
from weni import Tool
from weni.context import Context
from weni.events.event import Event
from weni.responses import TextResponse

class MyTool(Tool):
    def execute(self, context: Context):
        result = do_work()

        self.register_event(Event(
            event_name="weni_nexus_data",  # MANDATORY: must always be this exact value
            key="order_placed",
            value_type="string",
            value="completed",
            metadata={"customer": "John Doe", "order_id": "order_123"},
        ))

        return TextResponse(data=result)
```

### Mandatory event_name

**`event_name` MUST always be `"weni_nexus_data"`.** This is required for Nexus/Datalake ingestion. Arbitrary `event_name` values are not supported. Use the `key` field to distinguish what the event represents (e.g., `"conversation_classification"`, `"order_placed"`).

### Event Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_name` | `str` | ✅ | **MUST** be `"weni_nexus_data"` |
| `key` | `str` | ✅ | Semantic identifier (e.g., `"order_placed"`, `"conversation_classification"`) |
| `value_type` | `str` | ✅ | Type of value: `"string"`, `"int"`, etc. |
| `value` | `Any` | ✅ | The event value |
| `metadata` | `dict` | ❌ | Additional context (default: `{}`) |
| `date` | `str` | ❌ | ISO 8601 date string (default: current time) |

### Multiple Events

Register as many events as needed per execution:

```python
self.register_event(Event(
    event_name="weni_nexus_data",
    key="tool_started",
    value_type="string",
    value="started",
    metadata={"exec_id": "exec_001"},
))

result = expensive_operation()

self.register_event(Event(
    event_name="weni_nexus_data",
    key="tool_completed",
    value_type="string",
    value="completed",
    metadata={"exec_id": "exec_001", "duration_ms": 150},
))
```

### Execution Isolation

Events are scoped to each tool execution. On AWS Lambda warm starts, events from a previous invocation are never carried over. Each `Tool.__new__()` starts with a clean event registry.

### Legacy API (Deprecated)

The static `Event.register()` method still works but is **deprecated** and will be removed in version 3.0.0:

```python
# ❌ Deprecated — emits warning
Event.register(Event(
    event_name="weni_nexus_data",
    key="my_event",
    value_type="string",
    value="hello",
))
```

**Non-negotiables**:
- MUST always set `event_name` to `"weni_nexus_data"`
- MUST use `self.register_event()` (the deprecated `Event.register()` emits warnings)
- SHOULD include relevant metadata (`contact_urn`, durations, error details)
- SHOULD standardize `key` values across tools for easier Datalake querying
- MUST use primitive types for `value` (`string`, `int`, `bool`)

## Validation Rules Reference

This section documents all validation constraints enforced by Weni CLI. Violations will cause deployment failures.

### Agent Field Constraints

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `name` | string | ✅ | Maximum **55** characters |
| `description` | string | ✅ | No length limit, but conciseness recommended |
| `instructions` | array | ❌ | Each item minimum **40** characters |
| `guardrails` | array | ❌ | Each item minimum **40** characters |
| `tools` | array | ✅ | At least one tool required |
| `credentials` | object | ❌ | See Credentials Configuration |
| `constants` | object | ❌ | See Constants Configuration |
| `components` | array | ❌ | See Component Types |

### Tool Field Constraints

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `name` | string | ✅ | Maximum **40** characters |
| `description` | string | ✅ | Maximum **200** characters |
| `source.path` | string | ✅ | Valid directory path |
| `source.entrypoint` | string | ✅ | Format: `module.ClassName` |
| `source.path_test` | string | ❌ | Path to test YAML file |
| `parameters` | array | ❌ | Array of parameter objects |

### Parameter Field Constraints

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `description` | string | ✅ | Describes parameter purpose |
| `type` | string | ✅ | One of: `string`, `number`, `integer`, `boolean`, `array` |
| `required` | boolean | ❌ | Default: false |
| `contact_field` | boolean | ❌ | See Contact Field Constraints |

### Contact Field Constraints

When `contact_field: true`, the parameter name MUST comply with these rules:

**Name Format**:
- MUST match regex: `^[a-z][a-z0-9_]*$`
- MUST start with lowercase letter
- MAY contain only lowercase letters, numbers, and underscores
- Maximum **36** characters

**Reserved Names** (CANNOT be used):
```
id, name, first_name, language, groups, uuid, created_on, created_by,
modified_by, is, has, mailto, ext, facebook, jiochat, line, tel, telegram,
twilio, twitter, twitterid, viber, vk, fcm, whatsapp, wechat, freshchat,
rocketchat, discord, weniwebchat, instagram, slack, teams
```

**Example - Valid Contact Field**:
```yaml
parameters:
  - customer_email:
      description: "Customer's email address"
      type: "string"
      required: true
      contact_field: true    # ✅ Valid: lowercase, starts with letter
```

**Example - Invalid Contact Field**:
```yaml
parameters:
  - Name:                    # ❌ Invalid: starts with uppercase
      contact_field: true
  - first_name:              # ❌ Invalid: reserved name
      contact_field: true
  - 123abc:                  # ❌ Invalid: starts with number
      contact_field: true
```

### Credentials Configuration

Credentials allow tools to access secrets securely. Define them at the agent level.

**Required Credential Fields**:
- `label`: String, human-readable name for Weni UI
- `placeholder`: String, example text or hint

**Optional Credential Fields**:
- `is_confidential`: Boolean (default: true), masks value in UI

**Example**:
```yaml
agents:
  my_agent:
    credentials:
      api_key:
        label: "API Key"
        placeholder: "your-api-key-here"
        is_confidential: true
      base_url:
        label: "Base URL"
        placeholder: "https://api.example.com"
        is_confidential: false
    # ... rest of agent definition
```

**Accessing in Tools**:
```python
def execute(self, context: Context) -> TextResponse:
    api_key = context.credentials.get("api_key", "")
    base_url = context.credentials.get("base_url", "")
```

### Constants Configuration

Constants are reusable, non-sensitive configuration values defined at the agent level and shared across all tools of that agent. Unlike credentials, constants are for **public configuration** (API endpoints, feature flags, display preferences).

**Constant Types**:

| Type | Purpose | Required Fields |
|------|---------|-----------------|
| `text` | Free-form text with max length | `label`, `type`, `max_length`, `required`, `default` |
| `select` | Dropdown selection | `label`, `type`, `options`, `required`, `default` |
| `radio` | Radio button selection | `label`, `type`, `options`, `required`, `default` |
| `checkbox` | Checkbox selection | `label`, `type`, `options`, `required`, `default` |

**Text Type Example**:
```yaml
agents:
  my_agent:
    constants:
      API_ENDPOINT:
        label: "API Endpoint"
        type: "text"
        max_length: 255
        required: true
        default: "https://api.example.com"
```

**Select/Radio/Checkbox Type Example**:
```yaml
agents:
  my_agent:
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
        default: "INFO"
        required: true
```

**Accessing in Tools**:
```python
def execute(self, context: Context) -> TextResponse:
    endpoint = context.constants.get("API_ENDPOINT", "https://api.example.com")
    log_level = context.constants.get("LOG_LEVEL", "INFO")
```

**Constants vs Credentials**:
- **Constants**: Non-sensitive (API URLs, feature flags, limits, display settings)
- **Credentials**: Sensitive (API keys, tokens, passwords)

**Validation Rules for Constants**:
- MUST have `label` (string)
- MUST have `type` (one of: `text`, `select`, `radio`, `checkbox`)
- MUST have `default` value
- MUST have `required` field (boolean)
- Text constants MUST have `max_length` (integer > 0)
- Option-based constants MUST have non-empty `options` array
- Each option MUST have `label` and `value` (both strings)

### Component Types

Components can be added to agent definitions for specialized UI interactions:

| Component Type | Description |
|----------------|-------------|
| `cta_message` | Call-to-action URL buttons |
| `quick_replies` | Quick reply buttons |
| `list_message` | Interactive list selection |
| `catalog` | Product catalog display |
| `simple_text` | Basic text messages |

**Example**:
```yaml
agents:
  my_agent:
    components:
      - type: "quick_replies"
        instructions: "Use quick replies for yes/no questions"
      - type: "list_message"
        instructions: "Use lists when presenting multiple options"
```

## Local Development Files

For local testing with `weni run`, the CLI reads optional files from the tool directory.

### .env File (Credentials and Constants)

Located in tool folder (e.g., `tools/my_tool/.env`):
```bash
# Credentials
api_key=your-development-api-key
api_secret=your-development-secret

# Constants (fallback if defaults are not used)
API_ENDPOINT=https://dev.api.example.com
LOG_LEVEL=DEBUG
```

Credentials are accessed via `context.credentials.get("api_key")`.
Constants are accessed via `context.constants.get("API_ENDPOINT")` (or fall back to `default` from YAML if absent).

### .globals File (Global Configuration)

Located in tool folder (e.g., `tools/my_tool/.globals`):
```bash
environment=development
feature_flag=enabled
```

Accessed via `context.globals.get("environment")` in your tool.

## Weni Agents Toolkit Reference

### Tool Implementation Pattern

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse, FinalResponse
from weni.broadcasts import Text
from weni.events.event import Event


class MyToolName(Tool):
    def execute(self, context: Context) -> TextResponse:
        # 1. Extract parameters from context
        param_value = context.parameters.get("param_name", "default")

        # 2. Access credentials (sensitive) and constants (non-sensitive)
        api_key = context.credentials.get("api_key", "")
        endpoint = context.constants.get("API_ENDPOINT", "https://api.example.com")

        # 3. Optional: send broadcast for real-time feedback
        self.send_broadcast(Text(text="Processing..."))

        # 4. Perform business logic
        result = self.do_something(param_value, api_key, endpoint)

        # 5. Optional: register analytics event
        self.register_event(Event(
            event_name="weni_nexus_data",
            key="my_tool_executed",
            value_type="string",
            value="success",
            metadata={"param": param_value},
        ))

        # 6. Return appropriate response
        return TextResponse(data=result)

    def do_something(self, param: str, api_key: str, endpoint: str) -> dict:
        """Helper method for business logic."""
        return {"result": param}
```

### Available Components (from `weni.components`)

Components define how responses are displayed. Used internally by Response types.

| Component | Purpose |
|-----------|---------|
| `Text` | Text message content |
| `Header` | Message header (text or attachment) |
| `Footer` | Message footer text |
| `Attachments` | File/image attachments |
| `QuickReplies` | Quick reply buttons |
| `ListMessage` | Interactive list selection |
| `CTAMessage` | Call-to-action URL button |
| `Location` | Location request |
| `OrderDetails` | E-commerce order details |

### PreProcessor Implementation (Optional)

PreProcessors transform input data before agent processing:

```python
from weni.preprocessor import PreProcessor
from weni.preprocessor.preprocessor import ProcessedData
from weni.context.preprocessor_context import PreProcessorContext


class MyPreProcessor(PreProcessor):
    def process(self, context: PreProcessorContext) -> ProcessedData:
        # Access input data
        payload = context.payload
        params = context.params

        # Transform data
        processed = transform_data(payload)

        return ProcessedData(urn=context.urn, data=processed)
```

## Weni Flows API Integration

Tools can interact with the Weni Flows platform via the v2 API. Authentication is handled through the project's auth token, which is accessible via `context.project.get("auth_token")`.

### Authentication Pattern

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests


class CallFlowsApi(Tool):
    def execute(self, context: Context) -> TextResponse:
        auth_token = context.project.get("auth_token")

        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        response = requests.get(
            "https://flows.weni.ai/api/v2/contacts.json",
            headers=headers,
            params={"urn": "tel:+5511999999999"},
        )
        response.raise_for_status()
        return TextResponse(data=response.json())
```

**Non-negotiables**:
- MUST authenticate with `Authorization: Bearer <auth_token>` header
- MUST use `context.project.get("auth_token")` — never hardcode tokens
- MUST handle HTTP errors gracefully (use try/except + `raise_for_status`)
- SHOULD use query parameters for filtering (`before`, `after`, `uuid`, etc.)

### Available API Endpoints

Base URL: `https://flows.weni.ai/api/v2/`

---

#### Contacts

**GET** `/contacts.json` — List contacts

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | A contact UUID to filter by. ex: `09d23a05-47fe-11e4-bfe9-b8f6b119e9ab` |
| `urn` | No | A contact URN to filter by. ex: `tel:+250788123123` |
| `search` | No | A contact URN or name to search by |
| `group` | No | A group name or UUID to filter by. ex: `Customers` |
| `deleted` | No | Whether to return only deleted contacts. ex: `false` |
| `before` | No | Only return contacts modified before this date. ex: `2015-01-28T18:00:00.000` |
| `after` | No | Only return contacts modified after this date. ex: `2015-01-28T18:00:00.000` |
| `order_by` | No | Date field to order by (`created_on` or `modified_on`) |
| `limit` | No | Maximum number of objects to return. ex: `50` |

**POST** `/contacts.json` — Create or update contact

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | UUID of the contact to update |
| `urn` | No | URN of the contact to update. ex: `tel:+250788123123` |

| Body Field | Required | Description |
|------------|----------|-------------|
| `name` | No | Contact display name |
| `language` | No | Preferred language (3-letter ISO code). ex: `fre`, `eng` |
| `urns` | No | List of URNs belonging to the contact |
| `groups` | No | List of UUIDs of groups the contact belongs to |
| `fields` | No | Custom fields as a JSON dictionary |

```json
{"name": "Ben Haggerty", "groups": [], "urns": ["tel:+250788123123"]}
```

**DELETE** `/contacts.json` — Delete contact

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | UUID of the contact to delete |
| `urn` | No | URN of the contact to delete. ex: `tel:+250788123123` |

**GET** `/contacts_lean.json` — Lightweight contacts listing

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | A contact UUID to filter by |
| `search` | No | A contact URN or name to search by |
| `group` | No | A group name or UUID to filter by |
| `deleted` | No | Whether to return only deleted contacts |
| `before` | No | Only return contacts modified before this date |
| `after` | No | Only return contacts modified after this date |
| `order_by` | No | Date field to order by (`created_on` or `modified_on`) |
| `limit` | No | Maximum number of objects to return |

**GET** `/contacts_elastic.json` — ElasticSearch-based contact search

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `project_uuid` | **Yes** | Project UUID. ex: `09d23a05-47fe-11e4-bfe9-b8f6b119e9ab` |
| `name` | No | Filter by contact name. ex: `John` |
| `number` | No | Filter by partial or full phone number. ex: `12345` |
| `page_size` | No | Number of contacts per page. ex: `10` |
| `page_number` | No | Page number. ex: `1` |

**POST** `/contact_actions.json` — Bulk update contacts

| Body Field | Required | Description |
|------------|----------|-------------|
| `contacts` | **Yes** | The UUIDs of the contacts to update |
| `action` | **Yes** | One of: `add`, `remove`, `block`, `unblock`, `interrupt`, `archive_messages`, `delete`, `archive` |
| `group` | No | The UUID or name of a contact group |

**GET** `/contact_templates.json` — List templates for contacts

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `contact` | No | A contact UUID to filter by |
| `group` | No | A group UUID to filter by |
| `before` | No | Only return contacts modified before this date |
| `after` | No | Only return contacts modified after this date |

---

#### Fields (Custom Contact Fields)

**GET** `/fields.json` — List fields

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `key` | No | A field key to filter by. ex: `nick_name` |

**POST** `/fields.json` — Create or update field

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `key` | No | Key of an existing field to update |

| Body Field | Required | Description |
|------------|----------|-------------|
| `label` | **Yes** | The label of the field |
| `value_type` | **Yes** | The value type of the field |

---

#### Groups

**GET** `/groups.json` — List contact groups

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | A contact group UUID to filter by |
| `name` | No | A contact group name to filter by |

**POST** `/groups.json` — Create or update group

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | The UUID of the contact group to update |

| Body Field | Required | Description |
|------------|----------|-------------|
| `name` | **Yes** | The name of the contact group |

**DELETE** `/groups.json` — Delete group

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | **Yes** | The UUID of the contact group to delete |

---

#### Flows

**GET** `/flows.json` — List flows

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | A flow UUID to filter by. ex: `5f05311e-8f81-4a67-a5b5-1501b6d6496a` |
| `before` | No | Only return flows modified before this date |
| `after` | No | Only return flows modified after this date |

**GET** `/flow_starts.json` — List flow starts

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `id` | No | Only return the flow start with this ID |
| `after` | No | Only return flow starts modified after this date |
| `before` | No | Only return flow starts modified before this date |

**POST** `/flow_starts.json` — Start contacts in a flow

| Body Field | Required | Description |
|------------|----------|-------------|
| `flow` | **Yes** | The UUID of the flow to start |
| `groups` | No | The UUIDs of any contact groups to start |
| `contacts` | No | The UUIDs of any contacts to start |
| `urns` | No | The URNs of any contacts to start |
| `restart_participants` | No | Whether to restart participants already in the flow |
| `extra` | No | Any extra parameters to pass to the flow start |

```json
{"flow": "f5901b62-ba76-4003-9c62-72fdacc1b7b7", "urns": ["twitter:sirmixalot"]}
```

**GET** `/runs.json` — List flow runs

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `id` | No | A run ID to filter by. ex: `123456` |
| `flow` | No | A flow UUID to filter by |
| `contact` | No | A contact UUID to filter by |
| `responded` | No | Whether to only return runs with contact responses |
| `before` | No | Only return runs modified before this date |
| `after` | No | Only return runs modified after this date |

**GET** `/flows_labels.json` — List flow labels

No parameters.

**GET** `/definitions.json` — Export flow/campaign definitions

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `flow` | No | One or more flow UUIDs to include |
| `campaign` | No | One or more campaign UUIDs to include |
| `dependencies` | No | Whether to include dependencies. ex: `false` |

---

#### Broadcasts (Platform-Level)

> **Note**: These platform-level broadcasts are different from the tool-level `self.send_broadcast()` pattern. Platform broadcasts are fire-and-forget API calls to send messages to many contacts; tool broadcasts are real-time messages during a single tool execution.

**GET** `/broadcasts.json` — List broadcasts

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `id` | No | A broadcast ID to filter by. ex: `123456` |
| `before` | No | Only return broadcasts created before this date |
| `after` | No | Only return broadcasts created after this date |

**POST** `/broadcasts.json` — Send broadcast

| Body Field | Required | Description |
|------------|----------|-------------|
| `text` | **Yes** | The text of the message to send |
| `urns` | No | The URNs of contacts to send to |
| `contacts` | No | The UUIDs of contacts to send to |
| `groups` | No | The UUIDs of contact groups to send to |

**GET** `/whatsapp_broadcasts.json` — List WhatsApp broadcasts

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `id` | No | A broadcast ID to filter by. ex: `123456` |
| `before` | No | Only return broadcasts created before this date |
| `after` | No | Only return broadcasts created after this date |

**POST** `/whatsapp_broadcasts.json` — Send WhatsApp broadcast with templates

| Body Field | Required | Description |
|------------|----------|-------------|
| `urns` | No | The URNs of contacts to send to |
| `contacts` | No | The UUIDs of contacts to send to |
| `groups` | No | The UUIDs of contact groups to send to |
| `msg` | **Yes** | The template, text, and attachments to send |
| `template` | No | The template to use |
| `uuid` | **Yes** | The UUID of the template |
| `variables` | No | Variables for the template body |
| `locale` | No | Template locale (e.g., `pt-BR`, `en-US`) |
| `attachments` | No | Attachments to send. ex: `["image/png:https://example.com/image.png"]` |

---

#### Campaigns

**GET** `/campaigns.json` — List campaigns

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | A campaign UUID to filter by |

**POST** `/campaigns.json` — Create or update campaign

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | UUID of the campaign to update |

| Body Field | Required | Description |
|------------|----------|-------------|
| `name` | **Yes** | The name of the campaign |
| `group` | **Yes** | The UUID of the contact group operated on by the campaign |

**GET** `/campaign_events.json` — List campaign events

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | A campaign event UUID to filter by |
| `campaign` | No | A campaign UUID or name to filter by |

**POST** `/campaign_events.json` — Create or update campaign event

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | The UUID of the campaign event to update |

| Body Field | Required | Description |
|------------|----------|-------------|
| `campaign` | No | The UUID of the campaign this event belongs to |
| `relative_to` | **Yes** | The key of the contact field this event is relative to (string) |
| `offset` | **Yes** | The offset from the relative_to field value (integer, positive or negative) |
| `unit` | **Yes** | Unit of the offset: `minutes`, `hours`, `days`, `weeks` |
| `delivery_hour` | **Yes** | Hour to trigger (integer, `-1` for same hour, or `0`–`23`) |
| `message` | No | Message to send when triggered (string) |
| `flow` | No | UUID of the flow to start when triggered (string) |

**DELETE** `/campaign_events.json` — Delete campaign event

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | The UUID of the campaign event to delete |

---

#### Messages

**GET** `/messages.json` — List messages

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `id` | No | A message ID to filter by. ex: `123456` |
| `broadcast` | No | A broadcast ID to filter by. ex: `12345` |
| `contact` | No | A contact UUID to filter by |
| `urn` | No | A contact URN to filter by. ex: `tel:+12065551212` |
| `folder` | No | Folder name: `inbox`, `flows`, `archived`, `outbox`, `sent`, `incoming` |
| `label` | No | A label name or UUID to filter by. ex: `Spam` |
| `before` | No | Only return messages created before this date |
| `after` | No | Only return messages created after this date |

**POST** `/message_actions.json` — Bulk update messages

| Body Field | Required | Description |
|------------|----------|-------------|
| `messages` | **Yes** | The IDs of the messages to update |
| `action` | **Yes** | One of: `label`, `unlabel`, `archive`, `restore`, `delete` |
| `label` | No | The UUID or name of a message label |

---

#### Labels (Message Labels)

**GET** `/labels.json` — List message labels

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | A message label UUID to filter by |
| `name` | No | A message label name to filter by |

**POST** `/labels.json` — Create or update message label

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | The UUID of the message label to update |

| Body Field | Required | Description |
|------------|----------|-------------|
| `name` | **Yes** | The name of the message label |

**DELETE** `/labels.json` — Delete message label

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | **Yes** | The UUID of the message label to delete |

---

#### Templates

**GET** `/templates.json` — List WhatsApp templates

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `name` | No | A template name to filter by. ex: `MyTemplate` |
| `uuid` | No | Only return template with this UUID |
| `status` | No | Only return templates with this status. ex: `R` |

**GET** `/filter_templates.json` — Filter templates for contacts context

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `template` | No | Filter by template name. ex: `template_test` |
| `before` | No | Only return contacts for this template before date |
| `after` | No | Only return contacts for this template after date |

---

#### Tickets & Support

**GET** `/ticketers.json` — List ticketers

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | A ticketer UUID to filter by |
| `before` | No | Only return ticketers created before this date |
| `after` | No | Only return ticketers created after this date |

**GET** `/tickets.json` — List tickets

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `contact` | No | A contact UUID to filter by |

**POST** `/ticket_actions.json` — Update multiple tickets

| Body Field | Required | Description |
|------------|----------|-------------|
| `tickets` | **Yes** | The UUIDs of the tickets to update |
| `action` | **Yes** | One of: `assign`, `add_note`, `change_topic`, `close`, `reopen` |
| `assignee` | No | The email address of a user |
| `note` | No | The note text |

**GET** `/topics.json` — List topics

No parameters.

**POST** `/topics.json` — Create or update topic

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | The UUID of the topic to update |

| Body Field | Required | Description |
|------------|----------|-------------|
| `name` | **Yes** | The name of the topic |

---

#### Channels & Channel Events

**GET** `/channels.json` — List channels

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | A channel UUID to filter by. ex: `09d23a05-47fe-11e4-bfe9-b8f6b119e9ab` |
| `address` | No | A channel address to filter by. ex: `+250783530001` |

**GET** `/channel_events.json` — List channel events

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `id` | No | An event ID to filter by. ex: `12345` |
| `contact` | No | A contact UUID to filter by |
| `before` | No | Only return events created before this date |
| `after` | No | Only return events created after this date |

**GET** `/channel_stats.json` — Channel statistics

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | **Yes** | A channel UUID to filter by |

---

#### Globals (Flows Platform Globals)

> **Note**: These are Flows platform globals, different from tool `context.globals`.

**GET** `/globals.json` — List globals

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `before` | No | Only return globals modified before this date |
| `after` | No | Only return globals modified after this date |
| `key` | No | A global key to filter by |

**POST** `/globals.json` — Create or update global

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `key` | No | Key of an existing global to update |

| Body Field | Required | Description |
|------------|----------|-------------|
| `name` | No | The name value of the global |
| `value` | **Yes** | The new value of the global |

---

#### WhatsApp Flows

**GET** `/whatsapp_flows.json` — List WhatsApp Flows

No parameters.

---

#### Datalake Events (Weni Analytics)

**GET** `/events.json` — List datalake events

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `date_start` | **Yes** | Start date for filter. ex: `2025-06-03T00:00:00Z` |
| `date_end` | **Yes** | End date for filter. ex: `2025-06-20T23:59:59Z` |
| `key` | No | A key to filter by |
| `contact_urn` | No | A contact URN to filter by |
| `value_type` | No | A value_type to filter by |
| `value` | No | A value to filter by |
| `metadata` | No | A metadata to filter by |
| `event_name` | No | An event_name to filter by |
| `silver` | No | If true, also include data from silver |
| `table` | No | Required when `silver=true`; silver table name |
| `limit` | No | Number of events to return (default: `100`) |
| `offset` | No | Offset for pagination (default: `0`) |

**GET** `/events_group_by.json` — List datalake events grouped by field

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `date_start` | **Yes** | Start date for filter. ex: `2025-06-03T00:00:00Z` |
| `date_end` | **Yes** | End date for filter. ex: `2025-06-20T23:59:59Z` |
| `key` | No | A key to filter by |
| `contact_urn` | No | A contact URN to filter by |
| `value_type` | No | A value_type to filter by |
| `value` | No | A value to filter by |
| `metadata` | No | A metadata to filter by |
| `event_name` | No | An event_name to filter by |
| `group_by` | No | Field to group by (default: `value`) |
| `silver` | No | If true, also include data from silver |
| `table` | No | Required when `silver=true`; silver table name |

---

#### Resthooks (Webhooks)

**GET** `/resthooks.json` — List resthooks

No parameters.

**GET** `/resthook_events.json` — List resthook events

No parameters.

**GET** `/resthook_subscribers.json` — List resthook subscribers

No parameters.

**POST** `/resthook_subscribers.json` — Add resthook subscriber

| Body Field | Required | Description |
|------------|----------|-------------|
| `resthook` | **Yes** | The slug for the resthook to subscribe to |
| `target_url` | **Yes** | The URL that will be called when the resthook is triggered |

```json
{"resthook": "new-report", "target_url": "https://zapier.com/handle/1515155"}
```

**DELETE** `/resthook_subscribers.json` — Delete resthook subscriber

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `id` | **Yes** | The ID of the subscriber to delete |

---

#### Other Endpoints

**GET** `/archives.json` — List archives

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `archive_type` | No | Filter by type: `run`, `message` |
| `period` | No | Filter by period: `daily`, `monthly` |

**GET** `/boundaries.json` — List administrative boundaries

No parameters.

**GET** `/classifiers.json` — List classifiers

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | A classifier UUID to filter by |
| `before` | No | Only return classifiers created before this date |
| `after` | No | Only return classifiers created after this date |

**GET** `/products.json` — List products

No parameters.

**GET** `/workspace.json` — View workspace

No parameters.

**GET** `/users.json` — List users

No parameters.

**GET** `/intelligences.json` — List intelligences

No parameters.

**GET** `/external_services.json` — List external services

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `uuid` | No | An external service UUID to filter by |
| `before` | No | Only return external services created before this date |
| `after` | No | Only return external services created after this date |

**GET** `/brain_info.json` — Weni Brain info

No parameters.

**GET** `/analytics/contacts/.json` — Contact analytics

| Query Parameter | Required | Description |
|-----------------|----------|-------------|
| `group` | No | A group name or UUID to filter by. ex: `Customers` |
| `deleted` | No | Whether to return only deleted contacts |
| `before` | No | Only return events created before this date |
| `after` | No | Only return events created after this date |

### Complete Example: Starting a Flow from a Tool

```python
from weni import Tool
from weni.context import Context
from weni.responses import FinalResponse
from weni.broadcasts import Text
import requests


class TriggerOrderConfirmationFlow(Tool):
    def execute(self, context: Context) -> FinalResponse:
        auth_token = context.project.get("auth_token")
        contact_urn = context.contact.get("urn", "")
        flow_uuid = context.constants.get("ORDER_CONFIRMATION_FLOW_UUID", "")
        order_id = context.parameters.get("order_id", "")

        self.send_broadcast(Text(text="Iniciando confirmação do seu pedido..."))

        try:
            response = requests.post(
                "https://flows.weni.ai/api/v2/flow_starts.json",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "flow": flow_uuid,
                    "urns": [contact_urn],
                    "restart_participants": True,
                    "extra": {"order_id": order_id},
                },
                timeout=10,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            self.send_broadcast(Text(
                text="Não consegui iniciar a confirmação agora. Tente novamente em instantes.",
            ))
            return FinalResponse()

        return FinalResponse()
```

### Best Practices for Flows API Calls

1. **Always use `context.project.get("auth_token")`** for authentication — never hardcode
2. **Set reasonable timeouts** on `requests` calls (e.g., `timeout=10`)
3. **Wrap API calls in try/except** to handle `requests.exceptions.RequestException` gracefully
4. **Use `response.raise_for_status()`** to detect HTTP errors
5. **Store flow UUIDs, group UUIDs, etc. as constants** (non-sensitive) for easy per-environment configuration
6. **Log relevant metadata via events** (`self.register_event()`) for observability

## Weni Retail Setup API (VTEX Proxy)

Some Weni projects have access to the **Retail Setup API** (`https://retailsetup.weni.ai/`), which acts as a proxy to VTEX APIs. This eliminates the need for VTEX credentials (appKey/appToken) in the agent — authentication is handled via the project's `auth_token`.

> **Important**: Not all projects have Retail Setup enabled. When designing an agent, the user MUST specify whether the project uses the Retail Setup proxy or direct VTEX API calls with credentials. If using the proxy, tools do NOT need VTEX credentials — only the `auth_token` from `context.project.get("auth_token")`.

### Authentication

All Retail Setup endpoints use Bearer token authentication with the project's `auth_token`:

```python
auth_token = context.project.get("auth_token")
headers = {
    "Authorization": f"Bearer {auth_token}",
    "Content-Type": "application/json",
}
```

> **Note**: Retail Setup uses `Bearer` prefix (not `Token` like the Flows API).

### Available Endpoints

Base URL: `https://retailsetup.weni.ai`

---

#### Get Store URL

**GET** `/vtex/projects/store-url/`

Returns the VTEX store URL configured for the project.

**Response (success)**:
```json
{"store_url": "https://www.osklen.com.br"}
```

**Response (not configured)**:
```json
{"detail": "Store URL not found in project configuration."}
```

---

#### Get VTEX Account Identifier

**GET** `/vtex/projects/account-identifier/`

Returns the full VTEX account details including account name, company info, trade policies, licenses, hosts, and sites. This is essential for retrieving trade policy data and store configuration.

**Response (key fields)**:
```json
{
    "isActive": true,
    "accountName": "bravtexgrocerystore",
    "name": "VTEX Grocery",
    "companyName": "VTEX Grocery",
    "tradingName": "VTEX Grocery",
    "hosts": ["grocery.bravtexstores.com.br"],
    "sites": [
        {
            "id": 48478,
            "name": "bravtexgrocerystore",
            "tradingName": "VTEX Grocery",
            "hosts": ["grocery.bravtexstores.com.br"]
        }
    ],
    "licenses": [
        {
            "id": 7,
            "name": "E-Commerce Unlimited",
            "isPurchased": true,
            "products": [{"id": 19, "name": "OMS"}, {"id": 2, "name": "Catalog"}]
        }
    ]
}
```

---

#### Get VTEX Account Name

**GET** `/api/projects/vtex-account`

Returns just the VTEX account name. This is typically used as part of the VTEX base URL (e.g., `https://{accountName}.vtexcommercestable.com.br/`).

**Response**:
```json
{"vtex_account": "bravtexgrocerystore"}
```

---

#### VTEX Proxy (Generic)

**POST** `/vtex/proxy/`

The main proxy endpoint. Forwards any request to the VTEX API on behalf of the project, handling VTEX authentication internally.

| Body Field | Required | Description |
|------------|----------|-------------|
| `method` | **Yes** | HTTP method: `GET`, `POST`, `PUT`, `PATCH`, `DELETE` |
| `path` | **Yes** | VTEX API path (e.g., `/api/oms/pvt/orders/?q=`) |
| `data` | No | Request body payload (for `POST`, `PUT`, `PATCH`) |

**Example — List orders**:
```python
response = requests.post(
    "https://retailsetup.weni.ai/vtex/proxy/",
    headers={
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    },
    json={
        "method": "GET",
        "path": "/api/oms/pvt/orders/?q=",
    },
    timeout=15,
)
```

**Example — Search by email**:
```python
response = requests.post(
    "https://retailsetup.weni.ai/vtex/proxy/",
    headers={
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    },
    json={
        "method": "GET",
        "path": "/api/oms/pvt/orders/?q=customer@email.com",
    },
    timeout=15,
)
```

**Example — POST with payload**:
```python
response = requests.post(
    "https://retailsetup.weni.ai/vtex/proxy/",
    headers={
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    },
    json={
        "method": "POST",
        "path": "/api/some/vtex/endpoint",
        "data": {"key": "value"},
    },
    timeout=15,
)
```

The proxy returns the same response body that the VTEX API would return directly.

### Proxy vs Direct VTEX Credentials

| Approach | When to Use | Auth Method | Needs VTEX Credentials? |
|----------|-------------|-------------|-------------------------|
| **Retail Setup Proxy** | Project has Retail Setup enabled | `Bearer {auth_token}` via `context.project.get("auth_token")` | No |
| **Direct VTEX API** | Project without Retail Setup | `X-VTEX-API-AppKey` + `X-VTEX-API-AppToken` via `context.credentials` | Yes |

**Non-negotiables**:
- MUST confirm with the user whether the project uses Retail Setup proxy or direct VTEX credentials
- MUST use `Bearer` prefix (not `Token`) for Retail Setup authentication
- MUST always send proxy requests as `POST` to `/vtex/proxy/`, regardless of the actual VTEX method (specified in the `method` field)
- MUST set reasonable timeouts (VTEX APIs can be slow; use `timeout=15` or higher)
- MUST handle cases where Retail Setup is not configured (e.g., `"Store URL not found"` responses)

## Agent Definition Specification

### Complete Passive Agent Structure

```yaml
agents:
  agent_key:
    name: "Agent Display Name"                    # Required, max 55 chars
    description: "Concise description of capabilities and when to use this agent."  # Required
    credentials:                                  # Optional — sensitive values
      api_key:
        label: "API Key"
        placeholder: "your-api-key"
        is_confidential: true
    constants:                                    # Optional — non-sensitive config
      API_ENDPOINT:
        label: "API Endpoint"
        type: "text"
        max_length: 255
        required: true
        default: "https://api.example.com"
      LOG_LEVEL:
        label: "Log Level"
        type: "select"
        options:
          - label: "Debug"
            value: "DEBUG"
          - label: "Info"
            value: "INFO"
        default: "INFO"
        required: true
    instructions:                                 # Optional
      - "First instruction with at least 40 characters for clarity and guidance"
      - "Second instruction with at least 40 characters for clarity and guidance"
    guardrails:                                   # Optional
      - "Guardrail statement with at least 40 characters to define boundaries"
    components:                                   # Optional
      - type: "quick_replies"
        instructions: "When to use quick replies"
    tools:                                        # Required, at least one
      - tool_key:
          name: "Tool Display Name"               # Required, max 40 chars
          source:
            path: "tools/tool_folder"             # Required
            entrypoint: "main.ToolClassName"      # Required
            path_test: "test_definition.yaml"     # Optional
          description: "Tool purpose, max 200 chars"  # Required, max 200 chars
          parameters:                             # Optional
            - param_name:
                description: "Parameter description"  # Required
                type: "string"                    # Required: string|number|integer|boolean|array
                required: true                    # Optional, default: false
                contact_field: false              # Optional, see Contact Field Constraints
```

### Active Agent Structure (Rules-Based)

Active Agents use rules and pre-processing for proactive behavior:

```yaml
agents:
  agent_key:
    name: "Agent Display Name"                    # Required, max 55 chars
    description: "Agent purpose"                  # Required
    language: "en"                                # Required for active agents (ISO code)
    credentials:                                  # Optional
      api_key:
        label: "API Key"
        placeholder: "your-api-key"
    rules:                                        # Required for active agents
      rule_key:
        display_name: "Rule Display Name"         # Required
        template: "template_name_no_spaces"       # Required, no whitespace
        start_condition: "When condition is met"  # Required
        example: "Example scenario"               # Required
        source:
          path: "rules/rule_folder"               # Required
          entrypoint: "main.RuleClassName"        # Required
    pre_processing:                               # Optional
      source:
        path: "pre_processors/processor"          # Required if pre_processing defined
        entrypoint: "processing.PreProcessor"     # Required if pre_processing defined
      result_examples_file: "result_example.json" # Required, must end in .json
```

**Supported Language Codes** (ISO format):
```
af, sq, ar, az, bn, bg, ca, zh_CN, zh_HK, zh_TW, hr, cs, da, nl, en, en_GB,
en_US, et, fil, fi, fr, de, el, gu, ha, he, hi, hu, id, ga, it, ja, kn, kk,
ko, ky_KG, lo, lv, lt, ml, mk, ms, mr, nb, fa, pl, pt_BR, pt_PT, pa, ro, ru,
sr, sk, sl, es, es_AR, es_ES, es_MX, sw, sv, ta, te, th, tr, uk, ur, uz, vi, zu
```

### Test Definition Structure

Each tool folder MAY contain a `test_definition.yaml` for local testing:

```yaml
tests:
  test_case_1:
    parameters:
      param_name: "test_value"
      another_param: "another_value"
  test_case_2:
    parameters:
      param_name: "different_value"
```

**Running Tests**:
```bash
weni run agent_definition.yaml <agent_key> <tool_key>
weni run agent_definition.yaml <agent_key> <tool_key> -v  # Verbose output
weni run agent_definition.yaml <agent_key> <tool_key> -f custom_test.yaml
```

## Project Structure

### Required Directory Layout

```text
project-root/
├── agent_definition.yaml          # Agent and tools configuration
├── requirements.txt               # Project-level dependencies
└── tools/                         # All tool implementations
    └── tool_name/                 # One folder per tool
        ├── main.py               # Tool class implementation
        ├── requirements.txt      # Tool-specific dependencies (pinned versions)
        ├── test_definition.yaml  # Tool test cases (optional)
        ├── .env                  # Local credentials + constants (git-ignored)
        └── .globals              # Local globals (git-ignored)
```

### Tool Folder Requirements

- Folder name MUST match `source.path` in `agent_definition.yaml`
- `main.py` MUST contain the Tool class specified in `source.entrypoint`
- `requirements.txt` MUST list all tool-specific dependencies with pinned versions
- Class name MUST use `PascalCase` (e.g., `GetOrderStatus`, `SendNotification`)
- `.env` and `.globals` files SHOULD be added to `.gitignore`

## Deployment & CLI Commands

### Weni CLI Workflow

```bash
# 1. Login to Weni platform
weni login

# 2. List available projects
weni project list

# 3. Select project to work with
weni project use <project-uuid>

# 4. Verify current project
weni project current

# 5. Deploy agent definition
weni project push agent_definition.yaml
```

**Note**: The CLI deploys collaborator agents only. To configure the Manager agent or adjust collaboration settings, use the Weni UI.

### Deployment Checklist

Before running `weni project push`:
- [ ] Agent `name` is ≤55 characters
- [ ] Agent `description` clearly states capabilities for Manager routing
- [ ] All `instructions` are ≥40 characters each
- [ ] All `guardrails` are ≥40 characters each
- [ ] Tool `name` is ≤40 characters
- [ ] Tool `description` is ≤200 characters
- [ ] All parameter types are valid (`string`, `number`, `integer`, `boolean`, `array`)
- [ ] Contact field names match regex `^[a-z][a-z0-9_]*$` and ≤36 chars
- [ ] Contact field names are not reserved
- [ ] Credential definitions have `label` and `placeholder`
- [ ] Constant definitions have `label`, `type`, `default`, `required` (and `max_length` for text or `options` for select/radio/checkbox)
- [ ] All `event_name` values in `register_event` are `"weni_nexus_data"`
- [ ] Tools using broadcasts return `FinalResponse()` to avoid duplicate messaging
- [ ] Flows API calls use `context.project.get("auth_token")` — never hardcoded tokens
- [ ] All tools have valid `main.py` with correct class
- [ ] All `requirements.txt` files have pinned dependency versions
- [ ] Tool paths match folder structure

## Agent Evaluation

Agent Evaluation allows you to automatically test your Weni agents by defining test plans with steps and expected results. An evaluator interacts with your agent and judges whether the responses meet the expected criteria.

### How It Works

1. **Initialization**: The evaluator reads your test plan (`agent_evaluation.yml`)
2. **Test execution**: For each test case, the evaluator sends prompts to your agent and collects responses
3. **Judgment**: The evaluator analyzes the conversation and determines if the expected results were observed
4. **Report**: Results are displayed in a summary table and a markdown report is saved to `evaluation_results/`

### Prerequisites

- Weni CLI installed and authenticated (`weni login`)
- A project selected (`weni project use <project-uuid>`)
- An active agent configured in your Weni project

### Initialize an Evaluation Plan

```bash
weni eval init
weni eval init --plan-dir <path_to_directory>
```

This generates a starter `agent_evaluation.yml`:

```yaml
tests:
  greeting:
    steps:
      - Send a greeting message to the agent
    expected_results:
      - Agent responds with a friendly greeting
```

### Plan File Structure

Each test has a unique key containing:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `steps` | list of strings | **Yes** | The sequence of actions/messages to send to the agent |
| `expected_results` | list of strings | **Yes** | The criteria used to judge the agent's responses |

### Writing Tests

**Single-turn test**:
```yaml
tests:
  greeting:
    steps:
      - Send a greeting "Hello!"
    expected_results:
      - Agent responds with a friendly greeting
```

**Multi-turn test**:
```yaml
tests:
  multi_turn_conversation:
    steps:
      - Ask "What are your business hours?"
      - Follow up with "And on weekends?"
    expected_results:
      - Agent provides business hours for weekdays
      - Agent maintains context and provides weekend hours
```

**Multiple expected results**:
```yaml
tests:
  product_inquiry:
    steps:
      - Ask "What products do you offer?"
    expected_results:
      - Agent provides information about available products
      - Response includes clear product descriptions
      - Agent offers to help with specific product questions
```

**Error handling test**:
```yaml
tests:
  error_handling:
    steps:
      - Send an unclear message "xyz123 !!!"
    expected_results:
      - Agent handles the unclear input gracefully
      - Agent asks for clarification or provides guidance
```

### Running Evaluations

```bash
weni eval run                                    # Run all tests
weni eval run --filter "greeting,product_inquiry" # Run specific tests
weni eval run --verbose                          # Detailed reasoning output
weni eval run --plan-dir <path_to_directory>     # Custom plan directory
```

### Understanding Results

After running, the CLI displays a results table:

| Test | Status |
|------|--------|
| greeting | PASS |
| product_inquiry | PASS |
| error_handling | FAIL |

A markdown summary report is automatically saved to `evaluation_results/` with a timestamp (e.g., `summary_20260326_190242.md`).

When using `--verbose`, the reasoning column shows the evaluator's explanation for each test verdict.

### Troubleshooting

- **"Could not find agent_evaluation.yml"**: Run `weni eval init` first, or specify the correct directory with `--plan-dir`
- **Authentication errors (401)**: Run `weni login` to refresh your token; verify project with `weni project current`
- **Evaluation timeout**: Check if the agent is active and properly configured in the Weni platform
- **Tests failing unexpectedly**: Use `--verbose` to see reasoning; ensure `expected_results` are clear and specific

## Error Handling

### Tool Error Handling Pattern

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests


class MyApiTool(Tool):
    def execute(self, context: Context) -> TextResponse:
        try:
            result = self.call_api(context)
            return TextResponse(data=result)
        except requests.exceptions.RequestException as e:
            return TextResponse(data={
                "error": True,
                "message": f"API request failed: {str(e)}"
            })

    def call_api(self, context: Context) -> dict:
        api_key = context.credentials.get("api_key", "")
        url = context.parameters.get("endpoint", "")

        response = requests.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
        response.raise_for_status()
        return response.json()
```

**Non-negotiables**:
- MUST catch and handle external API errors gracefully
- MUST return error information in Response `data`, not raise exceptions
- MUST log errors for debugging (use `print()` for local testing)
- MUST NOT expose sensitive credentials in error messages
- SHOULD set timeouts on external HTTP calls to prevent hanging

## Governance

This constitution supersedes all other coding practices within Weni Agent projects. All team members and contributors MUST comply with these standards.

**Amendment Process**:
1. Propose changes via PR to `.specify/memory/constitution.md`
2. Changes require review and approval from tech lead
3. Document version bump rationale (MAJOR/MINOR/PATCH)
4. Update dependent templates if principles change

**Versioning Policy**:
- MAJOR: Backward-incompatible changes to Tool patterns or Response types
- MINOR: New toolkit features, additional response types, expanded guidance
- PATCH: Clarifications, wording improvements, documentation fixes

**Compliance Review**:
- All PRs MUST verify tool implementations follow the Tool pattern
- Code reviews MUST check Response type usage compliance (especially `TextResponse` vs `FinalResponse`)
- Agent definitions MUST be validated against YAML schema
- Agent descriptions MUST be reviewed for Manager routing clarity
- Contact field names MUST comply with regex and reserved name restrictions
- Event registrations MUST use `event_name="weni_nexus_data"` and `self.register_event()`
- Dependencies MUST be pinned in `requirements.txt` files

**Official References**:
- Weni CLI: https://github.com/weni-ai/weni-cli
- Weni Agents Toolkit: https://github.com/weni-ai/agents-toolkit
- CLI Documentation: https://weni-ai.github.io/weni-cli/
- Tools: https://weni-ai.github.io/weni-cli/core-concepts/tools/
- Broadcasts: https://weni-ai.github.io/weni-cli/core-concepts/broadcasts/
- Events: https://weni-ai.github.io/weni-cli/core-concepts/events/
- FinalResponse: https://weni-ai.github.io/weni-cli/core-concepts/final-response/
- Constants: https://weni-ai.github.io/weni-cli/core-concepts/constants/
- Credentials: https://weni-ai.github.io/weni-cli/core-concepts/credentials/
- Contact Fields: https://weni-ai.github.io/weni-cli/core-concepts/contact-fields/
- Agent Evaluation: https://weni-ai.github.io/weni-cli/eval/evaluation/
- Flows API v2: https://flows.weni.ai/api/v2/explorer/
- Retail Setup API (VTEX Proxy): https://retailsetup.weni.ai/

**Version**: 1.5.0 | **Ratified**: 2026-01-02 | **Last Amended**: 2026-04-22
