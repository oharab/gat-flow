# Google Workspace Out-of-Office Manager

A Python script for managing out-of-office (vacation responder) messages in Google Workspace using Google APIs.

## Features

- Set vacation responder messages with custom subject and body
- Schedule vacation messages with start and end times
- Use predefined message templates (vacation, sick, conference, training)
- Restrict responses to contacts only or same domain users
- View current vacation responder status
- Disable vacation responder
- Secure OAuth2 authentication with token persistence

## Prerequisites

1. **Google Cloud Platform Setup**:
   - Create a Google Cloud Platform project
   - Enable the Gmail API
   - Create OAuth2 client credentials
   - Download the credentials JSON file as `credentials.json`

2. **Python Requirements**: Python 3.8 or higher

## Installation

1. Clone or download the project files
2. Install dependencies using uv:
   ```bash
   uv sync
   ```

## Configuration

1. Place your Google OAuth2 credentials file as `credentials.json` in the project directory
2. (Optional) Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
3. (Optional) Customize default settings in the `.env` file

## Usage

### Set Vacation Message

Basic usage:
```bash
uv run python main.py set --subject "Out of Office" --message "I'm currently away..."
```

With schedule:
```bash
uv run python main.py set \
  --subject "Vacation - Back Monday" \
  --message "I'm on vacation until Monday..." \
  --start "2024-01-15 09:00" \
  --end "2024-01-22 09:00"
```

Using templates:
```bash
uv run python main.py set --template vacation
```

With restrictions:
```bash
uv run python main.py set \
  --template sick \
  --contacts-only \
  --start "2024-01-15"
```

### Check Status
```bash
uv run python main.py status
```

### Disable Vacation Message
```bash
uv run python main.py disable
```

### List Available Templates
```bash
uv run python main.py templates
```

### Initialize Configuration
```bash
uv run python main.py init
```

### Revoke Authentication
```bash
uv run python main.py revoke
```

## Available Templates

- **vacation**: Standard vacation message
- **sick**: Medical leave message
- **conference**: Conference attendance message
- **training**: Training/education message

## Command Options

### Global Options
- `--config, -c`: Path to configuration file (.env)
- `--credentials`: Path to Google credentials JSON file
- `--token`: Path to token file

### Set Command Options
- `--subject, -s`: Vacation response subject line
- `--message, -m`: Vacation response message body
- `--template, -t`: Use predefined template
- `--start`: Start date/time (YYYY-MM-DD HH:MM or YYYY-MM-DD)
- `--end`: End date/time (YYYY-MM-DD HH:MM or YYYY-MM-DD)
- `--contacts-only`: Only send to contacts
- `--domain-only`: Only send to same domain users

## First-time Setup

1. Run the script for the first time:
   ```bash
   uv run python main.py status
   ```

2. Your web browser will open for Google OAuth2 authorization
3. Sign in with your Google Workspace account
4. Grant the requested Gmail permissions
5. The authentication token will be saved for future use

## Security

- OAuth2 credentials are stored locally in `credentials.json`
- Access tokens are stored in `token.json` and automatically refreshed
- Only requires Gmail settings permissions (no email content access)
- Tokens can be revoked using the `revoke` command

## Troubleshooting

- **"Credentials file not found"**: Ensure `credentials.json` is in the project directory
- **"Permission denied"**: Check that Gmail API is enabled in your Google Cloud project
- **"Invalid grant"**: Run `uv run python main.py revoke` and re-authenticate
- **"Template not found"**: Use `uv run python main.py templates` to see available templates