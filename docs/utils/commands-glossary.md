# Project Commands

These commands are fundamental for developing and deploying agents, allowing direct interaction with your project on the Weni platform. They help you manage your project workflow, from authentication to project selection and management.

| Command | Description |
|---------|-------------|
| `weni` | Displays the main features and available commands directly in the terminal. |
| `weni --version` | Displays the current version of the Weni CLI installed on your system. |
| `weni init` | Creates an initial setup ready for use and learning with Weni. |
| `weni login` | This is how authentication happens. Use it to authenticate according to your Weni platform account. |
| `weni project list` | Existing projects in your account will be listed using this command. |
| `weni project use [project_uuid]` | With this command you can choose a specific project to work with by providing its UUID. |
| `weni project current` | Use this to identify the project identifier you are currently working with. |
| `weni project push [agent_definition_file]` | This command allows you to deploy/update your agents using the specified agent definition file. |
| `weni run [agent definition file] [agent name] [tool name]` | Run a specific tool from a passive agent locally for testing purposes. |
| `weni run [agent definition file] [agent name]` | Run all rules from an active agent locally for testing purposes. |
| `weni run [agent definition file] [agent name] [rule name]` | Run a specific rule from an active agent locally for testing purposes. |
| `weni run [agent definition file] [agent name] [resource name] -v` | Run a tool or rule with verbose mode enabled, showing detailed logs for debugging. |