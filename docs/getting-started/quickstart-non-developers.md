# Quick Start for Non-Developers

This guide is designed for those who are new to coding or prefer a simplified approach to creating agents with Weni CLI.

## Prerequisites

Before you begin, make sure you have:

1. **Installed Weni CLI**
   - Follow the [installation guide](installation.md)

2. **Created a Weni Account**
   - Sign up at [Weni.ai](https://weni.ai/)
   - Ensure you have access to at least one project

## Step-by-Step Guide

### 1. Login to Weni

```bash
weni login
```

This will open your browser for authentication. After successful login, you can close the browser tab.

### 2. List Your Projects

```bash
weni project list
```

This command will show all projects you have access to. Note down the UUID of the project you want to work with.

### 3. Select Your Project

```bash
weni project use your-project-uuid
```

Replace `your-project-uuid` with the UUID from the project list.

### 4. Verify Current Project

```bash
weni project current
```

This ensures you're working with the correct project.

### 5. Create a Simple Agent

You can create a simple agent without writing any code by using our templates:

```bash
weni init
```

This command will:
1. Create the necessary folder structure
2. Generate a basic agent configuration
3. Set up a pre-built CEP skill

### 6. Deploy Your Agent

```bash
weni project push
```

That's it! Your agent is now deployed and ready to use.