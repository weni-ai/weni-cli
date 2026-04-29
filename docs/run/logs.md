# Logs

Fetch and filter execution logs for a specific agent tool.

## Usage

```bash
weni logs --agent <agent_key> --tool <tool_key> [--start-time ISO8601] [--end-time ISO8601] [--pattern TEXT]
```

### Options

- `--agent, -a` (required): Agent key in your definition (e.g. `cep_agent`).
- `--tool, -t` (required): Tool key (e.g. `get_address`).
- `--start-time, -s` (optional): ISO 8601 datetime. Examples:
  - `2024-01-01T00:00:00`
  - `2024-01-01T00:00:00.000Z`
- `--end-time, -e` (optional): ISO 8601 datetime, same formats as start.
- `--pattern, -p` (optional): Simple substring filter (case-sensitive). Regex (e.g. `%...%`) is not supported.

Supported datetime formats include:

- `YYYY-MM-DDTHH:MM:SS`
- `YYYY-MM-DDTHH:MM:SS.sss`
- With timezone suffix: `Z`, `+00:00`, etc.

### Pagination

If more logs are available, you'll be prompted to fetch more. Choose `p` to continue or `q` to stop.

### Performance notes

Log queries run against CloudWatch Logs Insights and may take a few seconds to return on the first page (typically 1–5 seconds depending on the time window and log volume). Narrower time windows return faster.

### Examples

```bash
# Basic
weni logs -a cep_agent -t get_address

# With time range
weni logs -a cep_agent -t get_address -s 2024-01-01T00:00:00 -e 2024-01-01T23:59:59

# With simple pattern
weni logs -a cep_agent -t get_address -p error
```

