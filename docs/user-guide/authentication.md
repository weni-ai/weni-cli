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

Your authentication token is stored securely in your home directory. Never share or expose your authentication information.

## Token Refresh

Tokens are automatically refreshed when needed. You don't need to manually re-login unless:

- You've logged out
- Your token was revoked
- You want to switch accounts

## Logout

To logout and remove your authentication:

1. Delete your configuration file
2. Run `weni login` again to authenticate with different credentials

## Troubleshooting

### Common Issues

1. **Browser Doesn't Open**
   - Use the URL displayed in the terminal
   - Check if you have a default browser configured

2. **Authentication Failures**
   - Verify your internet connection
   - Check if your account has the necessary permissions

### Security Best Practices

1. **Keep Your Token Safe**
   - Don't share your configuration file
   - Use appropriate file permissions
   - Don't expose the token in scripts or logs

2. **Regular Validation**
   - Periodically verify your authentication status
   - Update your credentials if you suspect any security issues
