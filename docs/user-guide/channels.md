# Channel Management

Channels are the communication pathways through which your agents interact with users. The Weni CLI allows you to create and configure custom external channels to extend your agent's reach beyond the standard platforms.

## What are Channels?

Channels represent the various communication platforms or custom endpoints where your agents can send and receive messages. While Weni Platform natively supports popular channels like WhatsApp, Instagram, and Facebook, you can also create custom external channels to integrate with proprietary systems or third-party services.

## Channel Types

Currently, the Weni CLI supports the following channel type:

- **E2 (External v2)**: Custom external channels that allow you to integrate with any API endpoint for sending and receiving messages.

The E2 channel is handled by the [ExternalV2 handler in Courier](https://github.com/weni-ai/courier/blob/main/handlers/externalv2/doc.md), which is the source of truth for template behavior and channel endpoints.

## Creating a Channel

To create a new channel, you'll need to:

1. Create a channel definition file in YAML format
2. Have a project selected (use `weni project use <project_uuid>`)
3. Run the channel creation command

### Command

```bash
weni channel create <channel_definition_file>
```

**Arguments:**

- `channel_definition_file`: Path to the YAML file containing your channel configuration

### Channel Definition Structure

A channel definition file must follow this structure:

```yaml
channels:
  - name: "My Custom Channel"
    channel_type: "E2"
    schemes:
      - "external"
    config:
      mo_response_content_type: "application/json"
      mo_response: '{"status": "ok"}'
      mt_response_check: ""
      send_url: "https://api.example.com/messages/send"
      send_method: "POST"
      send_template: |
        {
          "to": "{{.urn_path}}",
          "message": "{{.text}}",
          "message_id": "{{.id}}"
        }
      content_type: "application/json"
      receive_template: |
        {
          "messages": [
            {
              "id": "{{.messageId}}",
              "urn_path": "{{.from}}",
              "text": "{{.text}}"
            }
          ]
        }
      send_authorization: "Bearer YOUR_API_TOKEN"
```

### Configuration Fields

#### Root Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | The name of your channel (max 100 characters) |
| `channel_type` | string | Yes | Type of channel. Currently supports: `E2` |
| `schemes` | array | Yes | Communication schemes. Currently supports: `external` |
| `config` | object | Yes | Channel configuration object |

#### Config Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mo_response_content_type` | string | Yes | Content type for Mobile Originated (incoming) message responses. Options: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data` |
| `mo_response` | string | No | Response body to send when receiving messages from external source |
| `mt_response_check` | string | No | String that must be present in the external API response for a Mobile Terminated (outgoing) message to be considered successful |
| `send_url` | string | Yes | The API endpoint URL to send messages to (must start with http:// or https://) |
| `send_method` | string | Yes | HTTP method to use for sending messages. Options: `POST`, `GET`, `PUT`, `PATCH` |
| `send_template` | string | Yes | Template for the message payload when sending messages. Use variables like `{{.urn_path}}`, `{{.text}}`, `{{.id}}` |
| `content_type` | string | Yes | Content type for outgoing messages. Options: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data` |
| `receive_template` | string | Yes | Template mapping the incoming request into the format Courier expects. Must render a `messages` array |
| `send_authorization` | string | No | Authorization header value for authenticating with the external API |

#### Optional Config Fields

The ExternalV2 handler also accepts the fields below. The CLI passes them through to the channel configuration without validating them, so double-check the spelling and values.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `send_media_url` | string | `send_url` | Alternative URL used when sending attachments |
| `send_url_template` | string | – | Template that builds the send URL dynamically. When present, it takes precedence over `send_url` (which is still required by the CLI validation) |
| `send_attachment_in_parts` | string | `"false"` | When `"true"`, attachments are sent in separate requests from the text |

### Templates

Both `send_template` and `receive_template` use the Go [`text/template`](https://pkg.go.dev/text/template) syntax. Fields are accessed with a leading dot, such as `{{.text}}` or `{{.message.from.id}}`, and control structures like `{{if}}` and `{{range}}` are supported.

Even when `content_type` is `application/x-www-form-urlencoded`, `send_template` must render a JSON object. Courier converts each key into a form field.

**Send Template Variables** (for outgoing messages):

- `{{.id}}`: Message ID
- `{{.uuid}}`: Message UUID
- `{{.text}}`: Message text content
- `{{.attachments}}`: Array of attachments in the `type:url` format
- `{{.contact_urn}}`: Full contact URN
- `{{.urn}}`: URN object with `scheme`, `path`, `query`, `fragment`, `identity`, and `auth`
- `{{.urn_path}}`: URN path, such as the phone number
- `{{.urn_identity}}`: Full URN identity, such as `tel:+5511999999999`
- `{{.urn_auth}}`: URN authentication token, when available
- `{{.channel}}`: Channel address
- `{{.channel_uuid}}`: Channel UUID
- `{{.quick_replies}}`: Array of quick replies
- `{{.products}}`: Array of products for catalog messages
- `{{.header}}`, `{{.body}}`, `{{.footer}}`: Sections of a structured message
- `{{.header_type}}`, `{{.header_text}}`: Header settings
- `{{.action}}`, `{{.action_type}}`: Message action and action type
- `{{.send_catalog}}`: Flag indicating a catalog send
- `{{.interaction_type}}`: Interaction type
- `{{.list_message}}`, `{{.cta_message}}`, `{{.flow_message}}`, `{{.order_details_message}}`: Objects for interactive message types
- `{{.buttons}}`: Array of buttons

**Helper Functions** (available in templates):

| Function | Description | Example |
|----------|-------------|---------|
| `split` | Splits a string | `{{split .text " "}}` |
| `attType` | Returns the attachment type | `{{attType $att}}` returns `image` |
| `attURL` | Returns the attachment URL | `{{attURL $att}}` |
| `int64ToString` | Converts an int64 to string | `{{int64ToString .id}}` |
| `toString` | Converts an int64 to string | `{{toString .id}}` |

Example iterating over attachments:

```yaml
send_template: |
  {
    "to": "{{.urn_path}}",
    "message": "{{.text}}"
    {{if .attachments}},
    "attachments": [
      {{range $i, $att := .attachments}}{{if $i}},{{end}}
      {"type": "{{attType $att}}", "url": "{{attURL $att}}"}
      {{end}}
    ]
    {{end}}
  }
```

**Receive Template Structure** (for incoming messages):

The receive template gets the raw body sent by the external system and must render the structure Courier expects, which is always a `messages` array:

```json
{
  "messages": [
    {
      "id": "external_msg_id",
      "urn_path": "+5511999999999",
      "urn_identity": "tel:+5511999999999",
      "urn_auth": "optional_token",
      "contact_name": "Contact name",
      "date": "2023-12-01T10:30:00Z",
      "text": "Received message",
      "attachments": ["image:https://example.com/photo.jpg"]
    }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique message ID in the external system |
| `urn_path` | Yes | URN path, such as the phone number. Use `urn_identity` instead when you have the full URN |
| `urn_identity` | No | Full URN, such as `tel:+5511999999999` |
| `urn_auth` | No | Authentication token associated with the URN |
| `contact_name` | No | Contact name |
| `date` | No | Message date in RFC3339 format |
| `text` | No | Message text |
| `attachments` | No | Array of attachments in the `type:url` format |

When the external system sends several messages in a single request, use `range`:

```yaml
receive_template: |
  {
    "messages": [
      {{range $i, $msg := .messages}}{{if $i}},{{end}}
      {
        "id": "{{$msg.id}}",
        "urn_path": "{{$msg.from}}",
        "text": "{{$msg.text}}"
      }
      {{end}}
    ]
  }
```

### Channel Endpoints

After the channel is created, use the returned UUID to configure the external system. Replace `{uuid}` with the channel UUID and use the flows host of your environment.

| Purpose | Endpoint | Methods |
|---------|----------|---------|
| Receive messages | `https://flows.weni.ai/c/e2/{uuid}/receive` | `GET`, `POST` |
| Sent status | `https://flows.weni.ai/c/e2/{uuid}/sent?id={msg_id}` | `GET`, `POST` |
| Delivered status | `https://flows.weni.ai/c/e2/{uuid}/delivered?id={msg_id}` | `GET`, `POST` |
| Failed status | `https://flows.weni.ai/c/e2/{uuid}/failed?id={msg_id}` | `GET`, `POST` |
| Stop contact | `https://flows.weni.ai/c/e2/{uuid}/stopped` | `GET`, `POST` |

The receive endpoint accepts `application/json` or `multipart/form-data`. The stop contact endpoint expects a `from` parameter with the contact identifier.

## Example: Creating a Custom API Channel

Let's create a channel to integrate with a custom messaging API:

### Step 1: Create the channel definition file

Create a file named `my_channel.yaml`:

```yaml
channels:
  - name: "Custom API Channel"
    channel_type: "E2"
    schemes:
      - "external"
    config:
      mo_response_content_type: "application/json"
      mo_response: '{"success": true}'
      mt_response_check: "success"
      send_url: "https://messaging.example.com/api/v1/send"
      send_method: "POST"
      send_template: |
        {
          "recipient": "{{.urn_path}}",
          "content": "{{.text}}",
          "sender_id": "{{.channel}}",
          "message_id": "{{.id}}"
        }
      content_type: "application/json"
      receive_template: |
        {
          "messages": [
            {
              "id": "{{.message_id}}",
              "urn_path": "{{.sender}}",
              "text": "{{.content}}",
              "date": "{{.timestamp}}"
            }
          ]
        }
      send_authorization: "Bearer abc123xyz456"
```

### Step 2: Ensure you have a project selected

```bash
weni project list
weni project use <your_project_uuid>
```

### Step 3: Create the channel

```bash
weni channel create my_channel.yaml
```

The command prints the channel name and UUID. Use that UUID to configure the webhook on the external system, as described in [Channel Endpoints](#channel-endpoints).

## Best Practices

1. **Test your endpoint first**: Before creating a channel, ensure your API endpoint is working correctly
2. **Secure your credentials**: Never commit channel definition files with real API tokens to version control
3. **Use environment-specific files**: Maintain separate channel definitions for development, staging, and production
4. **Validate JSON templates**: Render your `send_template` and `receive_template` with real data and ensure the result is valid JSON
5. **Set `mt_response_check`**: It lets Courier detect failures returned with a 200 status code
6. **Document your mappings**: Keep notes on how your external API fields map to Weni's expected format

## Common Use Cases

- **Legacy system integration**: Connect agents to existing internal messaging systems
- **Custom notification services**: Integrate with specialized notification providers
- **Multi-channel aggregation**: Route messages through a custom aggregation service
- **Testing and development**: Create mock channels for local development and testing

## Troubleshooting

### "Channel definition path is required"
Make sure you provide the path to your YAML file as an argument to the command.

### "No project selected, please select a project first"
You need to select a project first using `weni project use <project_uuid>`.

### "Invalid channel definition"
Check that your YAML file follows the correct structure and all required fields are present. Review the configuration fields table above.

### URL validation errors
Ensure your `send_url` starts with `http://` or `https://`.

### "receive body template is empty" or "unable to parse receive body template"
The `receive_template` is missing or has invalid Go template syntax. Remember that fields need a leading dot, as in `{{.from}}`.

### Messages are received but no contact is created
The rendered `receive_template` is probably missing `urn_path` or `urn_identity`, or the output is not a `messages` array.

### "unable to decode request body" or "unsupported content type"
The external system is sending a body that doesn't match the expected content type. ExternalV2 accepts `application/json` and `multipart/form-data` on the receive endpoint.

## Next Steps

After creating a channel:

1. Test the integration by sending a message through your agent
2. Monitor the channel's behavior in the Weni Platform dashboard
3. Configure your agents to use the new channel
4. Set up proper error handling and logging on your external endpoint

For more information about configuring agents to use specific channels, see the [Agents documentation](agents.md).

