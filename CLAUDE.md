# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python script for managing out-of-office messages in Google Workspace using Google APIs. The script automates setting vacation responders for user email accounts.

## Development Commands

```bash
# Create virtual environment and install dependencies
uv sync

# Run the script
uv run python main.py

# Run with specific user
uv run python main.py --user user@domain.com

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

- **main.py**: Entry point script handling command-line arguments and orchestrating the vacation responder setup
- **gmail_api.py**: Core Google Gmail API integration for managing vacation settings
- **auth.py**: Google OAuth2 authentication handling and token management
- **config.py**: Configuration management for API credentials and default settings

## Google API Setup

- Requires Google Cloud Platform project with Gmail API enabled
- OAuth2 credentials file (credentials.json) needed in project root
- Service account or user authentication depending on deployment model
- Scopes required: `https://www.googleapis.com/auth/gmail.settings.basic`

## Authentication Flow

The script uses OAuth2 flow to authenticate with Google APIs. First run will prompt for browser authentication and store refresh tokens locally for subsequent runs.

## Key Dependencies

- `google-auth` and `google-auth-oauthlib` for authentication
- `google-api-python-client` for Gmail API interaction
- `click` or `argparse` for command-line interface