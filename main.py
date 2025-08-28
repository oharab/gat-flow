"""Entry point script for managing Google Workspace out-of-office messages."""

from datetime import datetime
from typing import Optional

import click

from auth import GoogleAuth
from config import Config
from gmail_api import GmailVacationManager


@click.group()
@click.option("--config", "-c", help="Path to configuration file (.env)")
@click.option("--credentials", help="Path to Google credentials JSON file")
@click.option("--token", help="Path to token file")
@click.pass_context
def cli(ctx, config: Optional[str], credentials: Optional[str], token: Optional[str]):
    """Google Workspace Out-of-Office Message Manager.
    
    Manage vacation responder settings for Gmail accounts using Google APIs.
    """
    ctx.ensure_object(dict)
    
    # Load configuration
    cfg = Config(config)
    ctx.obj["config"] = cfg
    
    # Initialize authentication
    creds_file = credentials or cfg.credentials_file
    token_file = token or cfg.token_file
    
    ctx.obj["auth"] = GoogleAuth(creds_file, token_file)
    ctx.obj["gmail"] = GmailVacationManager(ctx.obj["auth"])


@cli.command()
@click.option("--subject", "-s", help="Vacation response subject line")
@click.option("--message", "-m", help="Vacation response message body")
@click.option("--template", "-t", help="Use predefined template (vacation, sick, conference, training)")
@click.option("--start", help="Start date/time (YYYY-MM-DD HH:MM)")
@click.option("--end", help="End date/time (YYYY-MM-DD HH:MM)")
@click.option("--contacts-only", is_flag=True, help="Only send to contacts")
@click.option("--domain-only", is_flag=True, help="Only send to same domain users")
@click.pass_context
def set(ctx, subject: Optional[str], message: Optional[str], template: Optional[str],
        start: Optional[str], end: Optional[str], contacts_only: bool, domain_only: bool):
    """Set vacation responder message."""
    config = ctx.obj["config"]
    gmail = ctx.obj["gmail"]
    
    # Use template if specified
    if template:
        templates = config.get_message_templates()
        if template not in templates:
            available = ", ".join(templates.keys())
            click.echo(f"Invalid template. Available templates: {available}")
            return
        
        template_data = templates[template]
        subject = subject or template_data["subject"]
        message = message or template_data["message"]
    
    # Use defaults if not specified
    subject = subject or config.default_subject
    message = message or config.default_message
    
    # Parse dates if provided
    start_time = None
    end_time = None
    
    if start:
        try:
            start_time = datetime.strptime(start, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                start_time = datetime.strptime(start, "%Y-%m-%d")
            except ValueError:
                click.echo(f"Invalid start date format: {start}")
                return
    
    if end:
        try:
            end_time = datetime.strptime(end, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                end_time = datetime.strptime(end, "%Y-%m-%d")
            except ValueError:
                click.echo(f"Invalid end date format: {end}")
                return
    
    # Set vacation message
    success = gmail.set_vacation_message(
        subject=subject,
        message=message,
        start_time=start_time,
        end_time=end_time,
        contacts_only=contacts_only or config.default_contacts_only,
        domain_only=domain_only or config.default_domain_only
    )
    
    if success:
        click.echo("✓ Vacation message set successfully!")
    else:
        click.echo("✗ Failed to set vacation message.")


@cli.command()
@click.pass_context
def disable(ctx):
    """Disable vacation responder."""
    gmail = ctx.obj["gmail"]
    
    success = gmail.disable_vacation_message()
    
    if success:
        click.echo("✓ Vacation message disabled successfully!")
    else:
        click.echo("✗ Failed to disable vacation message.")


@cli.command()
@click.pass_context
def status(ctx):
    """Show current vacation responder status."""
    gmail = ctx.obj["gmail"]
    gmail.print_vacation_status()


@cli.command()
@click.pass_context
def templates(ctx):
    """List available message templates."""
    config = ctx.obj["config"]
    templates = config.get_message_templates()
    
    click.echo("\n=== Available Templates ===")
    for name, template in templates.items():
        click.echo(f"\n{name.upper()}:")
        click.echo(f"  Subject: {template['subject']}")
        click.echo(f"  Message: {template['message'][:100]}...")
    click.echo("\nUse --template <name> with the 'set' command to use a template.")


@cli.command()
@click.option("--file", "-f", default=".env.example", help="Output file path")
@click.pass_context
def init(ctx, file: str):
    """Create sample configuration file."""
    config = ctx.obj["config"]
    config.create_sample_env_file(file)


@cli.command()
@click.pass_context
def revoke(ctx):
    """Revoke stored authentication tokens."""
    auth = ctx.obj["auth"]
    
    if auth.revoke_token():
        click.echo("✓ Authentication tokens revoked successfully!")
    else:
        click.echo("✗ Failed to revoke tokens or no tokens found.")


@cli.command()
@click.pass_context
def reauth(ctx):
    """Force re-authentication with browser login."""
    auth = ctx.obj["auth"]
    
    try:
        auth.force_reauthentication()
        click.echo("✓ Re-authentication completed successfully!")
    except Exception as e:
        click.echo(f"✗ Re-authentication failed: {e}")


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.")
    except Exception as e:
        click.echo(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()