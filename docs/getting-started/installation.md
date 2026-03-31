# Installation Guide

This guide will help you install the Weni CLI tool on your system. We provide multiple installation methods: a quick installation via pip/uv and a manual installation for development purposes.

## Requirements

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

### Install via PIP

You can install the CLI directly using pip:

```bash
pip install weni-cli
```

### Install via uv

```bash
uv tool install weni-cli
```

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/weni-ai/weni-cli.git
cd weni-cli
```

2. Install dependencies and make the CLI executable:
```bash
uv sync
```

## Verifying Installation

After installation, verify that Weni CLI is properly installed, type the command `weni` in your terminal:

```bash
weni
```

If everything went well, your terminal should display something like this:

![Weni Command](../assets/weni_command.png)

## Troubleshooting

If you encounter any issues:

1. Check our [GitHub Issues](https://github.com/weni-ai/weni-cli/issues)
2. Create a new issue with:
   - Your operating system
   - Python version (`python --version`)
   - Error message
   - Steps to reproduce
