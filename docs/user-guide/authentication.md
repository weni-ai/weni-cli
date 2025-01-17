# Authentication

Learn how to authenticate with Weni CLI and manage your credentials.

## Login Process

Weni CLI uses OAuth2 for authentication. When you run the login command:

```bash
weni login
```

The following happens:

1. A local web server starts on your machine
2. Your default browser opens to the Weni login page
3. After successful login, you're redirected back to the local server
4. The CLI receives and stores your authentication token

## Token Storage

Your authentication token is stored in the `.weni_cli` file in your home directory:

- Linux/MacOS: `~/.weni_cli`
- Windows: `C:\Users\YourUsername\.weni_cli`

!!! warning
    Never share or commit your `.weni_cli` file as it contains sensitive authentication information.

## Environment-Specific Login

### Production Environment

By default, `weni login` authenticates against the production environment.

### Staging Environment

To authenticate against staging:

1. Configure your `.weni_cli` file for staging (see [Configuration Guide](../getting-started/configuration.md))
2. Run `weni login`
3. Use your staging environment credentials

## Token Refresh

Tokens are automatically refreshed when needed. You don't need to manually re-login unless:

- You've logged out
- Your token was revoked
- You want to switch accounts

## Logout

Currently, there's no explicit logout command. To logout:

1. Delete or edit your `.weni_cli` file
2. Run `weni login` again to authenticate with different credentials

## Troubleshooting

### Common Issues

1. **Browser Doesn't Open**
   - Use the URL displayed in the terminal
   - Check if you have a default browser configured

2. **Token Storage Issues**
   - Ensure you have write permissions in your home directory
   - Check if the `.weni_cli` file is writable

3. **Authentication Failures**
   - Verify your internet connection
   - Ensure you're using the correct environment (staging/production)
   - Check if your account has the necessary permissions

### Security Best Practices

1. **Keep Your Token Safe**
   - Don't share your `.weni_cli` file
   - Use appropriate file permissions
   - Don't expose the token in scripts or logs

2. **Environment Separation**
   - Use different accounts for staging and production
   - Keep staging and production configurations separate

3. **Regular Validation**
   - Periodically verify your authentication status
   - Update your credentials if you suspect any security issues
