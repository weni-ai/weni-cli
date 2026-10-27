# Contacts

## What Are Contacts?

The contacts integration lets your tools **read and update Flows contact records** during execution — using the same URN that identifies the person in the current conversation. This is useful when your tool needs to look up profile data (name, custom fields, groups) or persist information collected during the interaction back to Flows.

Think of it as a programmatic CRM bridge: your tool talks to Flows contacts API while the conversation is running, without hand-rolling HTTP requests or authentication.

> **Note — Contacts vs Contact Fields:** This page covers the **Contacts API** (`self.contact.get()` / `self.contact.update()`). For declaring persistent tool parameters in your agent YAML, see [Contact Fields](./contact-fields.md). The two features complement each other — contact fields store values from agent parameters; the contacts integration lets you read or write the full Flows contact record from Python.

## Why Contacts Matter

The contacts integration enables tools to:

- Read the current conversation contact from Flows (identity, custom fields, groups, status)
- Update contact attributes such as `name`, `language`, `groups`, and custom `fields`
- Personalize logic based on data already stored in Flows
- Persist data collected during a tool execution back to the contact profile
- Use the same ergonomic pattern as [broadcasts](./broadcasts.md) — facade + shorthand on every `Tool`

## Quick Start

Every `Tool` instance exposes the contacts integration in two equivalent ways:

**Shorthand**:

```python
from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

class MyTool(Tool):
    def execute(self, context: Context) -> TextResponse:
        contact = self.get_contact()
        self.update_contact(fields={"email": "user@example.com"})
        return TextResponse(data={"name": contact.get("name")})
```

**Facade** (same behavior, explicit namespace):

```python
class MyTool(Tool):
    def execute(self, context: Context) -> TextResponse:
        contact = self.contact.get()
        self.contact.update(fields={"email": "user@example.com"})
        return TextResponse(data={"name": contact.get("name")})
```

Both forms delegate to the shared Flows client for authentication and HTTP — no manual setup required.

## Integration API

| Access | Equivalent to | Description |
|--------|---------------|-------------|
| `self.get_contact(urn=None)` | `self.contact.get(urn=None)` | Retrieve a single contact by URN |
| `self.update_contact(payload)` | `self.contact.update(payload)` | Update with a dict payload (legacy shorthand) |
| `self.contact.get(urn=None)` | — | Retrieve a single contact by URN |
| `self.contact.update(payload=None, urn=None, **kwargs)` | — | Update with dict, kwargs, or both |

The facade is lazy-initialized on first access and cached for the duration of the tool execution.

## Contact URN Resolution

When you omit the `urn` argument, the integration resolves it from the execution context using this precedence:

1. `context.contact["urns"][0]` — first URN in the contact's URN list
2. `context.contact["urn"]` — single URN field
3. `context.parameters["contact_urn"]` — fallback from tool parameters

If no URN can be resolved, a configuration error is raised **before** any request is sent.

You can override the context URN explicitly:

```python
contact = self.contact.get(urn="whatsapp:5582999893640")
self.contact.update(fields={"email": "user@example.com"}, urn="whatsapp:5582999893640")
```

### WhatsApp Brazil 9th-digit retry

For WhatsApp Brazil URNs (`whatsapp:55...`), if the exact digits from context do not match a contact in Flows, the integration automatically retries with the alternate 9th-digit variant before failing. When a match is found via the alternate URN, that URN is used for subsequent operations in the same call (including update).

## Reading a Contact

`get()` returns the Flows contact object as a dictionary — not the raw list envelope:

```python
contact = self.get_contact()

name = contact.get("name")
email = contact.get("fields", {}).get("email")
groups = contact.get("groups", [])
```

#### Raises

| Error | When |
|-------|------|
| `ContactSenderConfigError` | Missing auth token or contact URN |
| `ContactNotFoundError` | No contact matches the URN (after 9th-digit retry, if applicable) |
| `ContactAmbiguousError` | More than one contact matches the URN |
| `ContactSenderError` | HTTP, network, or unexpected response failures |

## Updating a Contact

Updates are **update-only** — the integration verifies the contact exists before sending the write. It does not create new contacts implicitly.

### Payload shape

The update accepts any write attribute supported by the Flows contacts endpoint: `name`, `language`, `groups`, `fields`, and other compatible keys.

**Dict only**:

```python
self.contact.update({"fields": {"email": "user@example.com", "plan": "premium"}})
```

**Keyword arguments only**:

```python
self.contact.update(fields={"email": "user@example.com"}, name="Maria Silva")
```

**Hybrid** (dict + kwargs — kwargs win on conflict):

```python
self.contact.update(
    {"fields": {"email": "old@example.com"}},
    fields={"email": "new@example.com"},  # this value is sent
)
```

Custom fields are nested under `fields`:

```python
self.update_contact(fields={
    "email": "leonardo.amaral@vtex.com",
    "customer_id": "C-12345",
})
```

### Validation rules

- The merged payload must include **at least one attribute** — empty updates are rejected before calling Flows.
- When the contact is identified by URN in the query string, **`urns` must not appear in the body** — the integration raises a validation error if you include it.

#### Raises (in addition to get errors)

| Error | When |
|-------|------|
| `ContactValidationError` | Empty payload or `urns` present in the body |
| `ContactNotFoundError` | Contact does not exist (update is not attempted) |

## Complete Example

A tool that reads the contact's current email, asks for a new one via broadcast, and persists the update:

```python
from weni import Tool
from weni.context import Context
from weni.broadcasts import Text, QuickReply
from weni.contacts import ContactNotFoundError
from weni.responses import FinalResponse, TextResponse

class UpdateContactEmail(Tool):
    def execute(self, context: Context):
        new_email = context.parameters.get("email")

        try:
            contact = self.contact.get()
        except ContactNotFoundError:
            return TextResponse(data={"error": "Contact not found in Flows"})

        current_email = contact.get("fields", {}).get("email")

        if not new_email:
            self.send_broadcast(QuickReply(
                text=f"Your current email is {current_email or 'not set'}. Send the new address.",
                options=["Cancel"],
            ))
            return FinalResponse()

        updated = self.contact.update(fields={"email": new_email})

        self.send_broadcast(Text(text=f"Email updated to {updated['fields']['email']}."))
        return FinalResponse()
```

## Error Handling

All contacts errors subclass `ContactSenderError`, so a single catch covers every failure mode:

```python
from weni.contacts import (
    ContactAmbiguousError,
    ContactNotFoundError,
    ContactSenderConfigError,
    ContactSenderError,
    ContactValidationError,
)

try:
    self.contact.update(fields={"email": "user@example.com"})
except ContactValidationError:
    # Invalid payload (empty body, urns in body, etc.)
    ...
except ContactNotFoundError:
    # Contact does not exist in Flows
    ...
except ContactSenderConfigError:
    # Missing auth token or URN
    ...
except ContactSenderError:
    # HTTP, network, or other contacts failures
    ...
```

## Best Practices

When working with contacts:

1. **Prefer shorthand for simple tools**: `self.get_contact()` and `self.update_contact({"fields": {...}})` keep tool code concise; use `self.contact.update(..., **kwargs)` when you need keyword arguments or an explicit URN override.
2. **Use `fields` for custom attributes**: Standard contact metadata (`name`, `language`, `groups`) goes at the top level; business-specific data belongs in `fields`.
3. **Handle not-found explicitly**: Updates never create contacts — catch `ContactNotFoundError` when the URN may not exist yet in Flows.
4. **Combine with broadcasts**: Send a confirmation broadcast after updating contact data, and return `FinalResponse()` so the agent does not duplicate the message. See [FinalResponse](./final-response.md).
5. **Do not include `urns` in update bodies**: Identify the contact via context or the `urn` argument; putting `urns` in the payload is rejected by design.
6. **Pair with Contact Fields when appropriate**: Use [Contact Fields](./contact-fields.md) for agent-declared persistent parameters; use the contacts integration when your tool logic needs direct read/write access to the Flows contact record.
