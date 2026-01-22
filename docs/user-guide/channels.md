# Channel Management

Channels are the communication pathways through which your agents interact with users. The Weni CLI allows you to create and configure custom external channels to extend your agent's reach beyond the standard platforms.

## What are Channels?

Channels represent the various communication platforms or custom endpoints where your agents can send and receive messages. While Weni Platform natively supports popular channels like WhatsApp, Instagram, and Facebook, you can also create custom external channels to integrate with proprietary systems or third-party services.

## Channel Types

Currently, the Weni CLI supports the following channel type:

- **E2 (External v2)**: Custom external channels that allow you to integrate with any API endpoint for sending and receiving messages.

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
          "to": "{{to}}",
          "message": "{{text}}",
          "from": "{{channel}}"
        }
      content_type: "application/json"
      receive_template: |
        {
          "from": "{{from}}",
          "text": "{{body.message}}",
          "date": "{{date}}"
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
| `mt_response_check` | string | No | Expression to validate Mobile Terminated (outgoing) message responses |
| `send_url` | string | Yes | The API endpoint URL to send messages to (must start with http:// or https://) |
| `send_method` | string | Yes | HTTP method to use for sending messages. Options: `POST`, `GET`, `PUT`, `PATCH` |
| `send_template` | string | Yes | JSON template for the message payload when sending messages. Use variables like `{{to}}`, `{{text}}`, `{{channel}}` |
| `content_type` | string | Yes | Content type for outgoing messages. Options: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data` |
| `receive_template` | string | Yes | JSON template mapping the incoming message format. Use variables like `{{from}}`, `{{body.message}}`, `{{date}}` |
| `send_authorization` | string | No | Authorization header value for authenticating with the external API |

### Template Variables

**Send Template Variables** (for outgoing messages):
- `{{to}}`: Recipient identifier
- `{{text}}`: Message text content
- `{{channel}}`: Channel identifier
- `{{id}}`: Message ID

**Receive Template Variables** (for incoming messages):
- `{{from}}`: Sender identifier
- `{{body.*}}`: Access fields from the incoming request body
- `{{date}}`: Message timestamp

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
      mt_response_check: ""
      send_url: "https://messaging.example.com/api/v1/send"
      send_method: "POST"
      send_template: |
        {
          "recipient": "{{to}}",
          "content": "{{text}}",
          "sender_id": "{{channel}}"
        }
      content_type: "application/json"
      receive_template: |
        {
          "from": "{{body.sender}}",
          "text": "{{body.content}}",
          "date": "{{body.timestamp}}"
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

## Best Practices

1. **Test your endpoint first**: Before creating a channel, ensure your API endpoint is working correctly
2. **Secure your credentials**: Never commit channel definition files with real API tokens to version control
3. **Use environment-specific files**: Maintain separate channel definitions for development, staging, and production
4. **Validate JSON templates**: Ensure your `send_template` and `receive_template` are valid JSON
5. **Document your mappings**: Keep notes on how your external API fields map to Weni's expected format

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

## Next Steps

After creating a channel:

1. Test the integration by sending a message through your agent
2. Monitor the channel's behavior in the Weni Platform dashboard
3. Configure your agents to use the new channel
4. Set up proper error handling and logging on your external endpoint

For more information about configuring agents to use specific channels, see the [Agents documentation](agents.md).

