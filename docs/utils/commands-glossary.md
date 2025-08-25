# Project Commands

These commands are fundamental for developing and deploying agents, allowing direct interaction with your project on the Weni platform. They help you manage your project workflow, from authentication to project selection and management.

| Command | Description |
|---------|-------------|
| `weni` | Displays the main features and available commands directly in the terminal. |
| `weni --version` | Displays the current version of the Weni CLI installed on your system. |
| `weni init` | Creates an initial setup ready for use and learning with Weni. |
| `weni login` | This is how authentication happens. Use it to authenticate according to your Weni platform account. |
| `weni project list` | Existing projects in your account will be listed using this command. |
| `weni project list --org <org_uuid>` | Lists only projects from the specified organization UUID. |
| `weni project use [project_uuid]` | With this command you can choose a specific project to work with by providing its UUID. |
| `weni project current` | Use this to identify the project identifier you are currently working with. |
| `weni project push [agent_definition_file] [--force-update]` | Deploy/update your agents using the specified agent definition file. |
| `weni run [agent_definition_file] [agent_key] [tool_key] [-f FILE] [-v]` | Run a specific tool from an agent locally. `-f/--file` lets you choose a test file; if omitted the CLI looks for `test_definition.yaml` in the tool folder. `-v` enables verbose logs. |
| `weni logs --agent <agent_key> --tool <tool_key> [--start-time ISO8601] [--end-time ISO8601] [--pattern TEXT]` | Fetch tool execution logs. Supports pagination and ISO 8601 date formats (e.g. `2024-01-01T00:00:00`). |