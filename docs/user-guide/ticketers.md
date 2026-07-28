# Ticketer Management

Ticketers connect your project to external ticket systems. The Weni CLI lets you create and configure generic ticketers from a YAML definition file, so agents and flows can open, forward, close, and reopen tickets through a partner HTTP service.

## What are Ticketers?

A ticketer is the platform integration that routes ticket operations between VTEX CX and an external system. When a flow opens a ticket, the platform calls your partner service. When an agent replies or closes a ticket in the partner UI, the partner sends webhooks back to the platform.

The **generic** ticketer type uses a documented HTTP contract: any service that implements the required endpoints can be registered without custom Mailroom code.

## Ticketer Types

Currently, the Weni CLI supports the following ticketer type:

- **generic**: HTTP-based integration with a partner ticketer service (open, forward, close, reopen, and history endpoints).

## Creating a Ticketer

To create a new ticketer, you need to:

1. Create a ticketer definition file in YAML format
2. Have a project selected (use `weni project use <project_uuid>`)
3. Run the ticketer creation command

### Command

```bash
weni ticketer create <ticketer_definition_file>
```

**Arguments:**

- `ticketer_definition_file`: Path to the YAML file containing your ticketer configuration

### Ticketer Definition Structure

A minimal ticketer definition (default HTTP contract, no custom templates):

```yaml
ticketers:
  - name: "Generic Ticketer Integration"
    ticketer_type: "generic"
    config:
      base_url: "https://your-ticketer-host"
      api_token: "<API_TOKEN>"
      skip_webhook_hmac: "yes"
      project_name: "my project"
      route_open: "/v1/tickets"
      route_forward: "/v1/tickets/{external_id}/messages"
      route_close: "/v1/tickets/{external_id}/close"
      route_reopen: "/v1/tickets/{external_id}/reopen"
      route_history: "/v1/tickets/{external_id}/history"
      route_history_message: "/v1/tickets/{external_id}/messages"
```

Only the first item in the `ticketers` array is used per command execution.

### Configuration Fields

#### Root Fields

| Field           | Type   | Required | Description                                       |
| --------------- | ------ | -------- | ------------------------------------------------- |
| `name`          | string | Yes      | Display name of the ticketer (max 100 characters) |
| `ticketer_type` | string | Yes      | Type of ticketer. Currently supports: `generic`   |
| `config`        | object | Yes      | Ticketer configuration object                     |

#### Config Fields — credentials and metadata

| Field               | Type   | Required    | Description                                                                                             |
| ------------------- | ------ | ----------- | ------------------------------------------------------------------------------------------------------- |
| `base_url`          | string | Yes         | Base URL of the partner ticketer service (must start with `http://` or `https://`)                      |
| `api_token`         | string | Yes         | Bearer token the platform uses when calling the partner service                                         |
| `webhook_secret`    | string | Conditional | Secret used to verify inbound webhooks from the partner. Required unless `skip_webhook_hmac` is enabled |
| `skip_webhook_hmac` | string | No          | Set to `true`, `1`, or `yes` to skip webhook HMAC verification                                          |
| `project_uuid`      | string | No          | Project UUID sent in ticket metadata. Auto-filled from the selected project when empty or omitted       |
| `project_name`      | string | No          | Project name sent in ticket metadata                                                                    |

#### Config Fields — routes

| Field                   | Type   | Required | Description                                                                                                      |
| ----------------------- | ------ | -------- | ---------------------------------------------------------------------------------------------------------------- |
| `route_open`            | string | No       | Override for the open-ticket endpoint. Default: `/v1/tickets`                                                    |
| `route_forward`         | string | No       | Override for forwarding messages. Default: `/v1/tickets/{external_id}/messages`                                  |
| `route_close`           | string | No       | Override for closing tickets. Default: `/v1/tickets/{external_id}/close`                                         |
| `route_reopen`          | string | No       | Override for reopening tickets. Default: `/v1/tickets/{external_id}/reopen`                                      |
| `route_history`         | string | No       | Override for batch history. Default: `/v1/tickets/{external_id}/history`                                         |
| `route_history_message` | string | No       | Override for one-by-one history. Default: same as `route_forward` (`/v1/tickets/{external_id}/messages`)         |

#### Config Fields — conversation history

| Field                | Type   | Required | Description                                                                                          |
| -------------------- | ------ | -------- | ---------------------------------------------------------------------------------------------------- |
| `history_mode`       | string | No       | How history is sent after open: `batch` (default) or `one_by_one`                                    |
| `history_batch_size` | string | No       | Max messages per batch request when `history_mode=batch`. Default: `50`                              |

| `history_mode`   | Endpoint used                         | Payload shape                                      |
| ---------------- | ------------------------------------- | -------------------------------------------------- |
| `batch`          | `route_history`                       | `HistoryRequest` with a `messages` array           |
| `one_by_one`     | `route_history_message` / `route_forward` | One `MessageRequest` per message (same as forward) |

#### Config Fields — payload templates

Optional [Go `text/template`](https://pkg.go.dev/text/template) strings that customize request or response bodies. When a template is absent or empty, the platform uses the default HTTP contract.

Helpers available in templates: `json` (serialize a value as JSON) and `toString`.

Prefer `{{json .field}}` for strings and nested objects so quotes, newlines, and `null` values stay valid JSON. If you expand objects field-by-field without `json`, keep `metadata.webhook_base_url` in `open_template` — the partner needs it to send agent replies back to the platform.

| Field                            | Direction                 | Description                                                                 |
| -------------------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `open_template`                  | Platform → Ticketer       | Replaces the default open-ticket request body                               |
| `open_response_template`         | Platform ← Ticketer       | Maps the partner open response to `{external_id, status, created_at}`       |
| `forward_template`               | Platform → Ticketer       | Replaces the default forward-message request body                           |
| `forward_response_template`      | Platform ← Ticketer       | Maps the partner forward response to `{message_external_id, status}`        |
| `close_template`                 | Platform → Ticketer       | Replaces the default close-ticket request body                              |
| `close_response_template`        | Platform ← Ticketer       | Maps the partner close response to `{status}`                               |
| `history_template`               | Platform → Ticketer       | Replaces the history request body (`batch` or `one_by_one` context)         |
| `history_response_template`      | Platform ← Ticketer       | Maps the partner history response to `{status, messages_received}`          |
| `messages_template`              | Ticketer → Platform       | Maps the inbound agent-message webhook body to the standard envelope        |
| `messages_response_template`     | Ticketer ← Platform       | Replaces the success response returned to the partner for agent messages    |
| `tickets_close_template`         | Ticketer → Platform       | Maps the inbound close webhook body to the standard envelope                |
| `tickets_close_response_template`| Ticketer ← Platform       | Replaces the success response returned to the partner for close webhooks    |

All `config` values must be strings.

### Integration Flow

```text
1. Platform opens ticket          → POST {base_url}{route_open}
2. Partner returns                → 201 { external_id }
3. Platform sends history         → batch: POST {base_url}{route_history}
                                    one_by_one: POST {base_url}{route_history_message} (per message)
4. Platform forwards new message  → POST {base_url}{route_forward}
5. Agent replies in partner       → POST {webhook_base_url}/messages
6. Agent closes in partner        → POST {webhook_base_url}/tickets/close
```

On ticket open, the platform includes `metadata.webhook_base_url` so the partner knows where to send inbound events.

## Example: Creating a Generic Ticketer

### Step 1: Prepare the partner service

Run your ticketer service and copy the credentials it exposes (for example, from server logs or a settings screen):

- `API_TOKEN` — used in `config.api_token`
- `WEBHOOK_SECRET` — used in `config.webhook_secret`

For local development, expose the service with a public URL (for example, ngrok) and use that URL as `base_url`.

### Step 2: Create the ticketer definition file

**Minimal** (default payloads and routes):

```yaml
ticketers:
  - name: "Generic Ticketer Integration"
    ticketer_type: "generic"
    config:
      base_url: "https://your-ticketer-host"
      api_token: "your-api-token"
      skip_webhook_hmac: "yes"
      project_name: "my org"
```

**With identity templates** (custom templates that recreate the default contract). Useful to validate template wiring without changing payload shape:

```yaml
ticketers:
  - name: "Generic Ticketer (equivalent templates)"
    ticketer_type: "generic"
    config:
      base_url: "https://your-ticketer-host"
      api_token: "your-api-token"
      skip_webhook_hmac: "yes"
      history_mode: "batch"
      history_batch_size: "50"
      open_template: |-
        {"ticket_id":{{json .ticket_id}},"topic":{{json .topic}},"contact":{{json .contact}},"body":{{json .body}},"assignee":{{json .assignee}},"metadata":{{json .metadata}},"opened_at":{{json .opened_at}}}
      open_response_template: |-
        {"external_id":{{json .external_id}},"status":{{json .status}},"created_at":{{json .created_at}}}
      forward_template: |-
        {"ticket_id":{{json .ticket_id}},"external_id":{{json .external_id}},"message_id":{{json .message_id}},"direction":{{json .direction}},"sender":{{json .sender}},"text":{{json .text}},"attachments":{{json .attachments}},"metadata":{{json .metadata}},"sent_at":{{json .sent_at}}}
      # … remaining templates (close, history, messages, tickets_close) follow the same pattern
```

**History one-by-one** (each history message posted to the forward endpoint):

```yaml
ticketers:
  - name: "Generic Ticketer (history one-by-one)"
    ticketer_type: "generic"
    config:
      base_url: "https://your-ticketer-host"
      api_token: "your-api-token"
      skip_webhook_hmac: "yes"
      history_mode: "one_by_one"
      route_history_message: "/v1/tickets/{external_id}/messages"
      # Same shape as forward_template (MessageRequest per message)
      history_template: |-
        {"ticket_id":{{json .ticket_id}},"external_id":{{json .external_id}},"message_id":{{json .message_id}},"direction":{{json .direction}},"sender":{{json .sender}},"text":{{json .text}},"attachments":{{json .attachments}},"metadata":{{json .metadata}},"sent_at":{{json .sent_at}}}
      # Partner usually replies with a forward-style body; map it to the history envelope
      history_response_template: |-
        {"status":"history_received","messages_received":1}
```

### Step 3: Ensure you have a project selected

```bash
weni project list
weni project use <your_project_uuid>
```

### Step 4: Create the ticketer

```bash
weni ticketer create my_ticketer.yaml
```

On success, the CLI displays the ticketer name and UUID.

## Best Practices

1. **Match routes to your partner API**: If you override `route_*` fields, ensure they match the endpoints your service actually exposes
2. **Secure your credentials**: Never commit ticketer definition files with real tokens to version control
3. **Use environment-specific files**: Maintain separate definitions for development, staging, and production
4. **Align HMAC settings**: If the partner runs with `SKIP_WEBHOOK_HMAC=true`, set `skip_webhook_hmac: "true"` in the ticketer config as well
5. **Preserve `webhook_base_url` in custom open templates**: When using `open_template`, include the full `metadata` object (for example with `{{json .metadata}}`) so agent replies can reach the platform
6. **Prefer `{{json …}}` in templates**: Avoid breaking JSON when values contain quotes, newlines, or are null
7. **Test the HTTP contract**: Validate open, history, forward, close, reopen, and webhook flows before using the ticketer in production flows

## Common Use Cases

- **Custom support desks**: Connect flows to an in-house ticketing UI
- **Partner integrations**: Plug in any HTTP service that implements the generic ticketer contract
- **Local development**: Register a local or tunneled reference service for end-to-end testing
- **Payload adapters**: Use templates when the partner API shape differs from the default contract without writing Mailroom code

## Troubleshooting

### "Ticketer definition path is required"

Provide the path to your YAML file as an argument to the command.

### "No project selected, please select a project first"

Select a project first using `weni project use <project_uuid>`.

### "'config.webhook_secret' is required unless 'config.skip_webhook_hmac' is set"

Add `webhook_secret` to your config, or set `skip_webhook_hmac: "true|yes|1"` when HMAC verification is disabled on both sides.

### "'config.\<field\>' is not a recognized field"

Only fields listed in this guide are accepted. Check spelling of template and route keys.

### URL validation errors

Ensure `base_url` starts with `http://` or `https://`.

### Agent replies do not reach the contact

Confirm the partner is calling the URL from `metadata.webhook_base_url` on open. If you customize `open_template`, do not drop that field from `metadata`.

### API errors after creation

The CLI calls `POST api/v1/ticketers` on the Weni CLI backend. If creation fails, confirm the backend endpoint is available and that your account has permission for the selected project.

## Next Steps

After creating a ticketer:

1. Use the returned UUID in flows or ticket actions that reference a ticketer
2. Open a test ticket and confirm the partner receives the open request
3. Confirm history delivery (`batch` or `one_by_one`) matches your `history_mode`
4. Verify agent replies and close events reach the platform through webhooks
5. Monitor ticket operations in the VTEX CX Platform dashboard

For the full HTTP contract your partner service must implement (endpoints, payloads, HMAC, and template context), see the generic ticketer service documentation in your integration repository (`generic-ticketer-service.md`).
