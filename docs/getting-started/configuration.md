# Configuration Guide

Learn how to configure Weni CLI for different environments and customize its behavior.

## Configuration File

Weni CLI uses a configuration file located in your home directory:

- Linux/MacOS: `~/.weni_cli`
- Windows: `C:\Users\YourUsername\.weni_cli`

!!! note
    The file is hidden by default (starts with a dot). You may need to show hidden files to see it.

## Environment Configuration

### Production Environment (Default)

The default configuration points to the production environment. The configuration file is created automatically after your first login.

### Staging Environment

To use the staging environment:

1. Create an account at [http://dash.stg.cloud.weni.ai/](http://dash.stg.cloud.weni.ai/)

2. Edit the `.weni_cli` file:

    === "Linux/MacOS"
        ```bash
        # Using nano
        nano ~/.weni_cli
        
        # Or using vim
        vim ~/.weni_cli
        ```

    === "Windows (Command Prompt)"
        ```batch
        notepad "%USERPROFILE%\.weni_cli"
        ```

    === "Windows (PowerShell)"
        ```powershell
        notepad "$env:USERPROFILE\.weni_cli"
        ```

3. Replace the contents with:
    ```json
    {
      "keycloak_url": "https://accounts.weni.ai/auth",
      "keycloak_realm": "weni-staging",
      "keycloak_client_id": "weni-cli",
      "weni_base_url": "https://api.stg.cloud.weni.ai",
      "nexus_base_url": "https://nexus.stg.cloud.weni.ai"
    }
    ```

4. Save the file and run `weni login` again

## Viewing Hidden Files

If you can't see the `.weni_cli` file:

=== "Linux/MacOS Terminal"
    ```bash
    ls -la ~
    ```

=== "Linux File Manager"
    Press ++ctrl+h++ or look for "Show Hidden Files" in the menu

=== "MacOS Finder"
    Press ++cmd+shift+dot++

=== "Windows File Explorer"
    1. Click on "View" in the ribbon
    2. Check "Hidden items" in the "Show/hide" section

## Configuration Options

The configuration file supports these settings:

| Setting | Description | Default |
|---------|-------------|---------|
| `keycloak_url` | Keycloak authentication URL | Production URL |
| `keycloak_realm` | Keycloak realm (staging/production) | Production realm |
| `keycloak_client_id` | Client ID for authentication | weni-cli |
| `weni_base_url` | Base URL for Weni API | Production API URL |
| `nexus_base_url` | Base URL for Nexus API | Production Nexus URL |

## Troubleshooting

### Common Issues

1. **File Permissions**
   - The `.weni_cli` file should be readable and writable by your user
   - Fix permissions: `chmod 600 ~/.weni_cli`

2. **Invalid JSON**
   - Ensure the file contains valid JSON
   - Use a JSON validator if needed

3. **Wrong Environment**
   - Check URLs in the configuration
   - Ensure you're using the correct realm

### Configuration Reset

To reset to default configuration:

1. Delete the `.weni_cli` file
2. Run `weni login` again

## Best Practices

1. **Backup Your Configuration**
   - Keep a backup of your working configuration
   - Document any custom settings

2. **Security**
   - Don't share your `.weni_cli` file
   - Keep file permissions restricted
   - Never commit the file to version control
