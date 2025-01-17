# Installation Guide

There are multiple ways to install the Weni CLI. Choose the method that best suits your needs.

## Requirements

Before installing, ensure you have:

- Python >= 3.12
- pip (Python package installer)
- Git (optional, for development installation)

## Installation Methods

### 1. Using pip (Recommended)

The simplest way to install Weni CLI is using pip:

```bash
pip install weni-cli
```

### 2. Development Installation

If you want to contribute or need the latest development version:

1. Clone the repository:
   ```bash
   git clone https://github.com/weni-ai/weni-cli.git
   cd weni-cli
   ```

2. Install using Poetry:
   ```bash
   poetry install
   ```

   Or using pip:
   ```bash
   pip install -e .
   ```

## Verifying Installation

After installation, verify that Weni CLI is properly installed:

```bash
weni --version
```

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade weni-cli
```

## Troubleshooting

### Common Issues

1. **Command not found**
   - Ensure Python's bin directory is in your PATH
   - Try using `python -m weni` instead

2. **Permission errors**
   - On Unix-like systems, you might need to use `sudo`
   - Or install in user space: `pip install --user weni-cli`

3. **Python version conflicts**
   - Use a virtual environment
   - Ensure you have Python 3.12 or newer

### Getting Help

If you encounter any issues:

1. Check our [GitHub Issues](https://github.com/weni-ai/weni-cli/issues)
2. Create a new issue with:
   - Your operating system
   - Python version (`python --version`)
   - Error message
   - Steps to reproduce
