# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python script for managing out-of-office messages and delegation in Google Workspace using Google APIs. Supports both OAuth2 authentication (personal accounts) and Service Account authentication (domain-wide delegation) for managing vacation responders and delegates across multiple users.

## Development Commands

```bash
# Create virtual environment and install dependencies
uv sync

# OAuth2 mode (opens browser)
uv run python main.py status

# Service Account mode (manage other users)  
uv run python main.py --service-account sa-key.json --user john@company.com status

# Auto-detect authentication method
uv run python main.py --auth-mode auto status

# Delegate management
uv run python main.py delegates                              # List delegates
uv run python main.py add-delegate delegate@company.com      # Add delegate
uv run python main.py remove-delegate delegate@company.com   # Remove delegate

# Run tests
uv run pytest tests/

# Run specific test
uv run pytest tests/test_gmail_api.py

# Lint and format code
uv run ruff check .

# Fix linting issues automatically
uv run ruff check --fix .

# Format code
uv run ruff format .

# Run all checks (lint + format)
uv run ruff check . && uv run ruff format .
```

## Architecture

- **main.py**: Entry point script with CLI interface supporting both OAuth2 and Service Account authentication
- **gmail_api.py**: Core Google Gmail API integration for managing vacation settings and delegates with user impersonation support
- **auth.py**: Flexible authentication system supporting OAuth2 and Service Account with domain-wide delegation
- **config.py**: Configuration management for API credentials, templates, and default settings

## Google API Setup

### OAuth2 Setup (Personal Use)
- Google Cloud Platform project with Gmail API enabled
- OAuth2 client credentials file (credentials.json) in project root
- First run opens browser for authentication, stores refresh token

### Service Account Setup (Domain-Wide)
- Service account key file (service-account-key.json) in project root  
- Domain-wide delegation enabled in Google Workspace Admin Console
- Required OAuth scopes: 
  - `https://www.googleapis.com/auth/gmail.settings.basic`
  - `https://www.googleapis.com/auth/gmail.settings.sharing`

## Authentication Modes

- **OAuth2**: Personal account management via browser authentication
- **Service Account**: Domain-wide management with user impersonation (no browser required)
- **Auto-detect**: Automatically selects authentication method based on available files

## Key Dependencies

- `google-auth` and `google-auth-oauthlib` for authentication
- `google-api-python-client` for Gmail API interaction
- `click` or `argparse` for command-line interface