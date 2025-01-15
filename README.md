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
  sample_agent:
    name: "Sample Agent"                                                                      # Maximum of 128 characters
    description: "Weni's sample agent"
    instructions:
      - "You should always be polite, respectful and helpful, even if the user is not."       # Minimum of 40 characters
      - "If you don't know the answer, don't lie. Tell the user you don't know."              # Minimum of 40 characters
    guardrails:
      - "Don't talk about politics, religion or any other sensitive topic. Keep it neutral."  # Minimum of 40 characters
    skills:
      - get_order_status:
          name: "Get Order Status"                                                            # Maximum of 53 characters
          path: "skills/order_status.zip"
          description: "Function to get the order status"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
      - get_order_details:
          name: "Get Order Details"                                                           # Maximum of 53 characters
          path: "skills/order_details.zip"
          description: "Function to get the order details"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
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
