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

A ticketer definition file must follow this structure:

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
```

Only the first item in the `ticketers` array is used per command execution.

### Configuration Fields

#### Root Fields


| Field           | Type   | Required | Description                                       |
| --------------- | ------ | -------- | ------------------------------------------------- |
| `name`          | string | Yes      | Display name of the ticketer (max 100 characters) |
| `ticketer_type` | string | Yes      | Type of ticketer. Currently supports: `generic`   |
| `config`        | object | Yes      | Ticketer configuration object                     |


#### Config Fields


| Field               | Type   | Required    | Description                                                                                             |
| ------------------- | ------ | ----------- | ------------------------------------------------------------------------------------------------------- |
| `base_url`          | string | Yes         | Base URL of the partner ticketer service (must start with `http://` or `https://`)                      |
| `api_token`         | string | Yes         | Bearer token the platform uses when calling the partner service                                         |
| `webhook_secret`    | string | Conditional | Secret used to verify inbound webhooks from the partner. Required unless `skip_webhook_hmac` is enabled |
| `skip_webhook_hmac` | string | No          | Set to `true`, `1`, or `yes` to skip webhook HMAC verification                                          |
| `project_uuid`      | string | No          | Project UUID sent in ticket metadata. Auto-filled from the selected project when empty or omitted       |
| `project_name`      | string | No          | Project name sent in ticket metadata                                                                    |
| `route_open`        | string | No          | Override for the open-ticket endpoint. Default: `/v1/tickets`                                           |
| `route_forward`     | string | No          | Override for forwarding messages. Default: `/v1/tickets/{external_id}/messages`                         |
| `route_close`       | string | No          | Override for closing tickets. Default: `/v1/tickets/{external_id}/close`                                |
| `route_reopen`      | string | No          | Override for reopening tickets. Default: `/v1/tickets/{external_id}/reopen`                             |
| `route_history`     | string | No          | Override for sending conversation history. Default: `/v1/tickets/{external_id}/history`                 |


All `config` values must be strings.

### Integration Flow

```text
1. Platform opens ticket     → POST {base_url}{route_open}
2. Partner returns           → 201 { external_id }
3. Platform forwards message → POST {base_url}{route_forward}
4. Agent replies in partner  → POST {webhook_base_url}/messages
5. Agent closes in partner   → POST {webhook_base_url}/tickets/close
```

On ticket open, the platform includes `metadata.webhook_base_url` so the partner knows where to send inbound events.

## Example: Creating a Generic Ticketer

### Step 1: Prepare the partner service

Run your ticketer service and copy the credentials it exposes (for example, from server logs or a settings screen):

- `API_TOKEN` — used in `config.api_token`
- `WEBHOOK_SECRET` — used in `config.webhook_secret`

For local development, expose the service with a public URL (for example, ngrok) and use that URL as `base_url`.

### Step 2: Create the ticketer definition file

Create a file named `my_ticketer.yaml`:

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

A reference file is available at `examples/generic_ticketer_definition.yaml` in the weni-cli repository.

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

1. **Match routes to your partner API**: If you override `route_`* fields, ensure they match the endpoints your service actually exposes
2. **Secure your credentials**: Never commit ticketer definition files with real tokens to version control
3. **Use environment-specific files**: Maintain separate definitions for development, staging, and production
4. **Align HMAC settings**: If the partner runs with `SKIP_WEBHOOK_HMAC=true`, set `skip_webhook_hmac: "true"` in the ticketer config as well
5. **Test the HTTP contract**: Validate open, forward, close, reopen, and webhook flows before using the ticketer in production flows

## Common Use Cases

- **Custom support desks**: Connect flows to an in-house ticketing UI
- **Partner integrations**: Plug in any HTTP service that implements the generic ticketer contract
- **Local development**: Register a local or tunneled reference service for end-to-end testing

## Troubleshooting

### "Ticketer definition path is required"

Provide the path to your YAML file as an argument to the command.

### "No project selected, please select a project first"

Select a project first using `weni project use <project_uuid>`.

### "'config.webhook_secret' is required unless 'config.skip_webhook_hmac' is set"

Add `webhook_secret` to your config, or set `skip_webhook_hmac: "true|yes|1"` when HMAC verification is disabled on both sides.

### URL validation errors

Ensure `base_url` starts with `http://` or `https://`.

### API errors after creation

The CLI calls `POST api/v1/ticketers` on the Weni CLI backend. If creation fails, confirm the backend endpoint is available and that your account has permission for the selected project.

## Next Steps

After creating a ticketer:

1. Use the returned UUID in flows or ticket actions that reference a ticketer
2. Open a test ticket and confirm the partner receives the open request
3. Verify agent replies and close events reach the platform through webhooks
4. Monitor ticket operations in the VTEX CX Platform dashboard

For the HTTP contract your partner service must implement, see the generic ticketer service documentation in your integration repository.