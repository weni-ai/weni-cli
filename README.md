# Weni-CLI

A command-line interface (CLI) tool to manage and interact with projects on the Weni platform.

## Features

- **Login**: Authenticate with Weni to access your projects.
- **List projects**: View a list of all projects available in your account.
- **Select project**: Set the project to be used by the CLI.
- **Current project**: Display information about the currently selected project.
- **Push project definition**: Upload the agents definition file to the selected project.

## Requirements

- Python >= 3.12
- Poetry >= 1.8.5

## Installation

### Install via PIP
You can install the CLI directly using pip:
```bash
pip install weni-cli
```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/weni-ai/weni-cli.git
   cd weni-cli
   ```

2. Install dependencies and make the CLI executable:
   ```bash
   poetry shell
   poetry install
   ```

## Usage

### 1. Login
Log in to your Weni account:
```bash
weni login
```

### 2. List projects
View all projects associated with your account:
```bash
weni project list
```

### 3. Select project
Choose the project you want to work with:
```bash
weni project use <project-uuid>
```

### 4. View current project
Check the currently configured project:
```bash
weni project current
```

### 5. Push project definition
Upload a YAML definition file to the configured project:
```bash
weni project push <definition_file.yaml>
```

## Examples

- Log in and list projects:
  ```bash
  weni login
  weni project list
  ```

- Set and check the current project:
  ```bash
  weni project use 12345678-1234-1234-1234-123456789012
  weni project current
  ```

- Push a definition file:
  ```bash
  weni project push definition.yaml
  ```

## Agent definition file example

```yaml
agents:
  my_agent:
    name: James
    description: "An agent to help users with orders status"
    instructions:
      - "Always be polite with the user, even if they are not polite"
      - "If the user asks for help, always try to help"
    guardrails:
      - "Do not talk about gambling"
    skills:
      - get_status:
          name: "Get status"
          path: "get_status.zip"
          description: "Get the status of an order"
          parameters:
            - arg1:
                description: "Argument 1 description"
                type: "string"
                required: true
  another_agent:
    name: Bond
    description: "An agent to help users with orders general information"
    skills:
      - get_order:
          name: "Get Order"
          path: "get_order.zip"
          description: "Get the order information"
          parameters:
            - arg1:
                description: "Argument 1 description"
                type: "string"
                required: false
```

## Contributing

Contributions are welcome! Follow the steps below to contribute:

1. Fork the repository.
2. Create a branch for your feature or bug fix:
   ```bash
   git checkout -b my-feature
   ```
3. Commit your changes:
   ```bash
   git commit -m "Description of my feature"
   ```
4. Push your branch:
   ```bash
   git push origin my-feature
   ```
5. Open a Pull Request in the original repository.
