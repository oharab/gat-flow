# Google Workspace Out-of-Office Manager

A Python CLI for managing Gmail vacation responders and mailbox delegates in Google Workspace.

Supports two authentication modes:

- **OAuth2** — sign in with your own Google account via the browser; manages your own mailbox only.
- **Service Account (domain-wide delegation)** — no browser; impersonates any user in your Workspace domain to manage their vacation responder and delegates.

## Features

- Set, view, and disable Gmail vacation responders
- Schedule vacation messages with start/end times
- Built-in templates (vacation, sick, conference, training) and custom templates stored in `.env`
- Restrict responses to contacts or same-domain users
- List, add, and remove Gmail delegates on any mailbox in the domain
- Built-in `setup`, `info`, and `troubleshoot` commands for diagnosing auth problems

## Prerequisites

- Python 3.13+
- A Google Cloud project with the Gmail API enabled
- Credentials for one of the two auth modes (see [Authentication Setup](#authentication-setup))

## Installation

```bash
uv sync
```

For full step-by-step setup instructions tailored to your auth mode:

```bash
uv run python main.py setup --type oauth2
uv run python main.py setup --type service-account
uv run python main.py setup --type both
```

## Authentication Setup

### OAuth2 (personal mailbox only)

1. In Google Cloud Console: **APIs & Services → Credentials → Create credentials → OAuth client ID → Desktop app**.
2. Download the JSON and save as `credentials.json` in the project root.
3. First run opens a browser to authorize; a refresh token is saved to `token.json`.

Required scope: `https://www.googleapis.com/auth/gmail.settings.basic`

### Service Account (domain-wide)

1. In Google Cloud Console: create a **service account** and a **JSON key**. Save the key as `service-account-key.json` in the project root.
2. In the service account settings, enable **domain-wide delegation** and note the client ID.
3. In Google Workspace Admin Console: **Security → API controls → Domain-wide delegation → Add new**. Enter the client ID and authorize these scopes:
   - `https://www.googleapis.com/auth/gmail.settings.basic`
   - `https://www.googleapis.com/auth/gmail.settings.sharing` (required for delegate management)
4. Every command then needs a `--user user@yourdomain.com` to identify the mailbox to act on.

## Commands

All commands accept the global options listed under [Global Options](#global-options). Commands that act on a mailbox also accept a per-command `--user` to override the global value.

### Vacation responder

| Command | Description |
|---|---|
| `status` | Show current vacation responder state for the user |
| `set` | Enable/update the vacation responder |
| `disable` | Turn the vacation responder off |
| `templates` | List built-in and custom message templates |
| `add-template` | Save a new custom template into `.env` |
| `remove-template` | Remove a custom template from `.env` |

### Delegate management (service account mode)

| Command | Description |
|---|---|
| `delegates` | List current delegates on the user's mailbox |
| `add-delegate DELEGATE_EMAIL` | Grant another user delegate access to the mailbox |
| `remove-delegate DELEGATE_EMAIL` | Revoke a delegate |

### Auth & diagnostics

| Command | Description |
|---|---|
| `info` | Show detected auth mode and config |
| `setup` | Print setup instructions (use `--type oauth2\|service-account\|both`) |
| `troubleshoot` | Diagnose common auth/config problems |
| `init` | Write a sample `.env` file |
| `reauth` | Force OAuth2 re-authentication (OAuth2 only) |
| `revoke` | Revoke stored OAuth2 tokens |

## Global Options

| Option | Description |
|---|---|
| `-c, --config TEXT` | Path to `.env` config file |
| `--oauth2-credentials TEXT` | Path to OAuth2 client credentials JSON (default `credentials.json`) |
| `--service-account TEXT` | Path to service account key JSON (default `service-account-key.json`) |
| `--token TEXT` | Path to OAuth2 token file (default `token.json`) |
| `-u, --user TEXT` | Email of the user to manage (required for service account mode) |
| `--auth-mode [oauth2\|service-account\|auto]` | Force a specific auth mode (default: auto-detect by which credentials file is present) |

## Command Options

### `set`

| Option | Description |
|---|---|
| `-s, --subject TEXT` | Subject line |
| `-m, --message TEXT` | Message body (HTML allowed) |
| `-t, --template TEXT` | Use a named template instead of `--subject`/`--message` |
| `--start TEXT` | Start date/time (`YYYY-MM-DD HH:MM` or `YYYY-MM-DD`) |
| `--end TEXT` | End date/time (`YYYY-MM-DD HH:MM` or `YYYY-MM-DD`) |
| `--contacts-only` | Only auto-reply to known contacts |
| `--domain-only` | Only auto-reply to users in the same domain |
| `--user TEXT` | Override the global `--user` for this command |

### `status`, `disable`, `delegates`, `add-delegate`, `remove-delegate`

All accept `--user TEXT` to override the global `--user`.

`add-delegate` and `remove-delegate` take the delegate's email as a positional argument: `DELEGATE_EMAIL`.

### `add-template`

| Option | Description |
|---|---|
| `--name TEXT` (required) | Template name (used with `set --template <name>`) |
| `--subject TEXT` (required) | Template subject line |
| `--message TEXT` (required) | Template message body |
| `-f, --file TEXT` | Env file to update (default `.env`) |

### `remove-template`

| Option | Description |
|---|---|
| `--name TEXT` (required) | Template to remove |
| `-f, --file TEXT` | Env file to update (default `.env`) |

### `init`

| Option | Description |
|---|---|
| `-f, --file TEXT` | Output path (default `.env.example`) |

### `setup`

| Option | Description |
|---|---|
| `-t, --type [oauth2\|service-account\|both]` | Which setup instructions to show |

## Examples

### OAuth2 mode (own mailbox)

```bash
# Check your own status (opens browser on first run)
uv run python main.py status

# Set a vacation message
uv run python main.py set --subject "Out of Office" --message "Back Monday."

# Use a template with a schedule
uv run python main.py set --template vacation \
  --start "2026-06-01 09:00" --end "2026-06-08 09:00"

# Disable
uv run python main.py disable
```

### Service account mode (any user in the domain)

```bash
# Status for another user
uv run python main.py status --user emma@example.com

# Set OOF on someone else's mailbox
uv run python main.py set \
  --user emma@example.com \
  --template vacation \
  --start "2026-06-01" --end "2026-06-08"

# List, add, and remove delegates
uv run python main.py delegates --user emma@example.com
uv run python main.py add-delegate ben@example.com --user emma@example.com
uv run python main.py remove-delegate ben@example.com --user emma@example.com
```

### Custom templates

```bash
uv run python main.py add-template \
  --name remote \
  --subject "Working remotely" \
  --message "I'm working remotely today and may be slow to respond."

uv run python main.py set --template remote
```

## Built-in Templates

- `vacation` — standard vacation message
- `sick` — medical leave
- `conference` — conference attendance
- `training` — training/education

List them (including any custom ones you've added) with `uv run python main.py templates`.

## Files

| File | Purpose |
|---|---|
| `credentials.json` | OAuth2 client secrets (OAuth2 mode) |
| `service-account-key.json` | Service account key (service account mode) |
| `token.json` | Saved OAuth2 refresh token |
| `.env` | Optional defaults and custom templates |

## Troubleshooting

Run the built-in diagnostic:

```bash
uv run python main.py troubleshoot
uv run python main.py info
```

Common issues:

- **`Client secrets must be for a web or installed app`** — `credentials.json` is actually a service account key. Rename it to `service-account-key.json` or pass `--service-account <path>`.
- **`unauthorized_client` / `access_denied` (service account)** — domain-wide delegation isn't authorized for the service account's client ID in Workspace Admin, or a required scope is missing.
- **Delegate command fails with 403** — the `gmail.settings.sharing` scope isn't authorized for the service account.
- **`Invalid grant` (OAuth2)** — run `uv run python main.py revoke` then retry.

## Development

```bash
uv sync --extra dev          # install pytest, ruff, etc.
uv run pytest                # unit tests only (fast, no network, no auth)
uv run pytest -m integration # integration tests (HttpMockSequence against real client)
uv run ruff check .
uv run ruff format .
```

Test layout:

- `tests/unit/` — pure-logic tests, no API or filesystem dependencies. Run by default.
- `tests/integration/` — exercise `gmail_api.py` against `googleapiclient.http.HttpMockSequence` so the real Google client handles URL construction and parameter validation. Skipped by default; opt in with `-m integration`.
- `tests/fixtures/gmail-discovery-v1.json` — vendored Gmail v1 discovery doc, not currently loaded at test time (the client ships its own static copy) but kept for reference.

## Security

- Service account keys and OAuth tokens stay on your machine; nothing is sent anywhere except Google's API.
- Tokens can be revoked with `revoke`.
- Required scopes are limited to Gmail *settings* — no email content access.
