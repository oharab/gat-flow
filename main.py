"""Entry point script for managing Google Workspace out-of-office messages."""

from datetime import datetime
from typing import Optional

import click

from auth import AuthManager, AuthenticationError, OAuth2Auth, ServiceAccountAuth
from config import Config
from gmail_api import GmailVacationManager


def _get_gmail_manager_for_user(ctx, user: Optional[str]) -> GmailVacationManager:
    """Get Gmail manager for specified user, with service account validation."""
    auth_handler = ctx.obj["auth"]
    target_user = user or ctx.obj["user_email"]
    
    # Validate that service account has a target user
    if isinstance(auth_handler, ServiceAccountAuth) and not target_user:
        raise click.ClickException(
            "Service Account mode requires specifying a user to manage.\n"
            "Use --user email@domain.com or set it globally before the command."
        )
    
    # Create Gmail manager with appropriate user
    if target_user != ctx.obj["user_email"]:
        return GmailVacationManager(auth_handler, target_user)
    else:
        return ctx.obj["gmail"]


@click.group()
@click.option("--config", "-c", help="Path to configuration file (.env)")
@click.option("--oauth2-credentials", help="Path to OAuth2 credentials JSON file")
@click.option("--service-account", help="Path to service account key JSON file")
@click.option("--token", help="Path to OAuth2 token file")
@click.option("--user", "-u", help="Email of user to manage (required for service account)")
@click.option("--auth-mode", type=click.Choice(['oauth2', 'service-account', 'auto']), 
              default='auto', help="Authentication mode to use")
@click.pass_context
def cli(ctx, config: Optional[str], oauth2_credentials: Optional[str], 
        service_account: Optional[str], token: Optional[str], user: Optional[str],
        auth_mode: str):
    """Google Workspace Out-of-Office Message Manager.
    
    Supports both OAuth2 (personal accounts) and Service Account (domain-wide) authentication.
    
    Examples:
    \b
      # OAuth2 mode (opens browser)
      python main.py status
      
      # Service account mode (manage other users)
      python main.py --service-account sa-key.json --user john@company.com status
      
      # Auto-detect authentication method
      python main.py --auth-mode auto status
    """
    ctx.ensure_object(dict)
    
    # Load configuration
    cfg = Config(config)
    ctx.obj["config"] = cfg
    ctx.obj["user_email"] = user
    
    # Skip authentication initialization for setup and init commands
    if ctx.invoked_subcommand in ['setup', 'init']:
        ctx.obj["auth"] = None
        ctx.obj["gmail"] = None
        return
    
    try:
        # Initialize authentication based on mode
        if auth_mode == 'oauth2':
            oauth2_file = oauth2_credentials or cfg.credentials_file
            token_file = token or cfg.token_file
            auth_handler = AuthManager.create_oauth2_auth(oauth2_file, token_file)
            
        elif auth_mode == 'service-account':
            sa_file = service_account or "service-account-key.json"
            auth_handler = AuthManager.create_service_account_auth(sa_file)
            
        else:  # auto mode
            oauth2_file = oauth2_credentials or cfg.credentials_file
            sa_file = service_account or "service-account-key.json"
            auth_handler = AuthManager.auto_detect_auth_type(oauth2_file, sa_file)
        
        ctx.obj["auth"] = auth_handler
        ctx.obj["gmail"] = GmailVacationManager(auth_handler, user)
        
    except AuthenticationError as e:
        click.echo(f"❌ Authentication Error: {e}")
        ctx.exit(1)
    except Exception as e:
        click.echo(f"❌ Initialization Error: {e}")
        ctx.exit(1)


@cli.command()
@click.option("--subject", "-s", help="Vacation response subject line")
@click.option("--message", "-m", help="Vacation response message body")
@click.option("--template", "-t", help="Use predefined template (vacation, sick, conference, training)")
@click.option("--start", help="Start date/time (YYYY-MM-DD HH:MM)")
@click.option("--end", help="End date/time (YYYY-MM-DD HH:MM)")
@click.option("--contacts-only", is_flag=True, help="Only send to contacts")
@click.option("--domain-only", is_flag=True, help="Only send to same domain users")
@click.option("--user", help="Email of user to manage (overrides global --user)")
@click.pass_context
def set(ctx, subject: Optional[str], message: Optional[str], template: Optional[str],
        start: Optional[str], end: Optional[str], contacts_only: bool, domain_only: bool,
        user: Optional[str]):
    """Set vacation responder message."""
    config = ctx.obj["config"]
    
    try:
        gmail = _get_gmail_manager_for_user(ctx, user)
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        return
    
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
    try:
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
    
    except AuthenticationError as e:
        click.echo(f"❌ Authentication Error: {e}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.command()
@click.option("--user", help="Email of user to manage (overrides global --user)")
@click.pass_context
def disable(ctx, user: Optional[str]):
    """Disable vacation responder."""
    try:
        gmail = _get_gmail_manager_for_user(ctx, user)
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        return
    
    try:
        success = gmail.disable_vacation_message()
        
        if success:
            click.echo("✓ Vacation message disabled successfully!")
        else:
            click.echo("✗ Failed to disable vacation message.")
    
    except AuthenticationError as e:
        click.echo(f"❌ Authentication Error: {e}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.command()
@click.option("--user", help="Email of user to manage (overrides global --user)")
@click.pass_context
def status(ctx, user: Optional[str]):
    """Show current vacation responder status."""
    try:
        gmail = _get_gmail_manager_for_user(ctx, user)
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        return
    
    try:
        gmail.print_vacation_status()
    
    except AuthenticationError as e:
        click.echo(f"❌ Authentication Error: {e}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


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
    """Force re-authentication (OAuth2 only)."""
    auth = ctx.obj["auth"]
    
    if not isinstance(auth, OAuth2Auth):
        click.echo("❌ Re-authentication only available for OAuth2 mode.")
        click.echo("   Service accounts use key files and don't need re-authentication.")
        return
    
    try:
        auth.force_reauthentication()
        click.echo("✓ Re-authentication completed successfully!")
    except Exception as e:
        click.echo(f"✗ Re-authentication failed: {e}")


@cli.command()
@click.pass_context
def info(ctx):
    """Show authentication and configuration information."""
    auth = ctx.obj["auth"]
    user_email = ctx.obj["user_email"]
    
    click.echo("\n=== Configuration Information ===")
    
    # Authentication info
    auth_type = "OAuth2" if isinstance(auth, OAuth2Auth) else "Service Account"
    click.echo(f"Authentication Type: {auth_type}")
    
    if isinstance(auth, OAuth2Auth):
        click.echo(f"Credentials File: {auth.credentials_file}")
        click.echo(f"Token File: {auth.token_file}")
        click.echo("User: Authenticated user (self)")
    else:
        click.echo(f"Service Account File: {auth.service_account_file}")
        if user_email:
            click.echo(f"Target User: {user_email}")
        else:
            click.echo("Target User: Not specified (use --user)")
    
    # Scopes
    click.echo(f"Required Scopes: {', '.join(auth.SCOPES)}")
    
    click.echo("=" * 35)


@cli.command()
@click.option("--type", "-t", type=click.Choice(['oauth2', 'service-account', 'both']), 
              default='both', help="Type of authentication setup to show")
@click.pass_context
def setup(ctx, type: str):
    """Show detailed instructions for setting up authentication files."""
    
    click.echo("\n" + "=" * 60)
    click.echo("🔧 GOOGLE API AUTHENTICATION SETUP INSTRUCTIONS")
    click.echo("=" * 60)
    
    if type in ['oauth2', 'both']:
        click.echo("\n📱 OAUTH2 SETUP (Personal Account Management)")
        click.echo("-" * 50)
        click.echo("Use this method to manage your own Gmail vacation settings.")
        click.echo()
        
        click.echo("1️⃣  CREATE GOOGLE CLOUD PROJECT:")
        click.echo("   • Go to: https://console.cloud.google.com")
        click.echo("   • Click 'Select a project' → 'New Project'")
        click.echo("   • Enter project name → Click 'Create'")
        click.echo()
        
        click.echo("2️⃣  ENABLE GMAIL API:")
        click.echo("   • In Google Cloud Console, go to 'APIs & Services' → 'Library'")
        click.echo("   • Search for 'Gmail API' → Click on it")
        click.echo("   • Click 'Enable'")
        click.echo()
        
        click.echo("3️⃣  CREATE OAUTH2 CREDENTIALS:")
        click.echo("   • Go to 'APIs & Services' → 'Credentials'")
        click.echo("   • Click '+ CREATE CREDENTIALS' → 'OAuth client ID'")
        click.echo("   • If prompted, configure OAuth consent screen:")
        click.echo("     - User Type: External (or Internal for Workspace)")
        click.echo("     - Fill required fields, add your email as test user")
        click.echo("   • Application type: 'Desktop application'")
        click.echo("   • Name: 'Gmail Vacation Manager' (or your choice)")
        click.echo("   • Click 'Create'")
        click.echo()
        
        click.echo("4️⃣  DOWNLOAD CREDENTIALS:")
        click.echo("   • Click the download button (⬇️) next to your OAuth client")
        click.echo("   • Save the JSON file as 'credentials.json' in this directory")
        click.echo()
        
        click.echo("✅ OAuth2 Setup Complete!")
        click.echo("   Run: python main.py status")
        click.echo("   (This will open your browser for first-time authentication)")
        
    if type in ['service-account', 'both']:
        if type == 'both':
            click.echo("\n" + "=" * 60)
        
        click.echo("\n🏢 SERVICE ACCOUNT SETUP (Domain-Wide Management)")
        click.echo("-" * 55)
        click.echo("Use this method to manage vacation settings for any user in your domain.")
        click.echo("⚠️  Requires Google Workspace admin privileges!")
        click.echo()
        
        click.echo("1️⃣  CREATE SERVICE ACCOUNT:")
        click.echo("   • In Google Cloud Console, go to 'IAM & Admin' → 'Service Accounts'")
        click.echo("   • Click '+ CREATE SERVICE ACCOUNT'")
        click.echo("   • Name: 'gmail-vacation-manager' (or your choice)")
        click.echo("   • Description: 'Manages Gmail vacation responders'")
        click.echo("   • Click 'Create and Continue' → 'Done'")
        click.echo()
        
        click.echo("2️⃣  GENERATE SERVICE ACCOUNT KEY:")
        click.echo("   • Click on the service account you just created")
        click.echo("   • Go to 'Keys' tab → 'ADD KEY' → 'Create new key'")
        click.echo("   • Key type: JSON → Click 'Create'")
        click.echo("   • Save the JSON file as 'service-account-key.json' in this directory")
        click.echo()
        
        click.echo("3️⃣  ENABLE DOMAIN-WIDE DELEGATION:")
        click.echo("   • In the service account details, check 'Enable G Suite Domain-wide Delegation'")
        click.echo("   • Product name: 'Gmail Vacation Manager'")
        click.echo("   • Click 'Save'")
        click.echo("   • Copy the 'Client ID' (you'll need it in step 4)")
        click.echo()
        
        click.echo("4️⃣  CONFIGURE DOMAIN-WIDE DELEGATION (Google Workspace Admin):")
        click.echo("   • Go to: https://admin.google.com")
        click.echo("   • Navigate to: Security → API Controls → Domain-wide Delegation")
        click.echo("   • Click 'Add new' → Enter the Client ID from step 3")
        click.echo("   • OAuth Scopes: https://www.googleapis.com/auth/gmail.settings.basic")
        click.echo("   • Click 'Authorize'")
        click.echo()
        
        click.echo("✅ Service Account Setup Complete!")
        click.echo("   Run: python main.py --service-account service-account-key.json --user user@domain.com status")
    
    click.echo("\n" + "=" * 60)
    click.echo("📂 EXPECTED FILES IN PROJECT DIRECTORY:")
    click.echo("-" * 40)
    if type in ['oauth2', 'both']:
        click.echo("• credentials.json          (OAuth2 client credentials)")
        click.echo("• token.json               (Auto-generated after first OAuth2 login)")
    if type in ['service-account', 'both']:
        click.echo("• service-account-key.json (Service account private key)")
    click.echo()
    
    click.echo("🔍 VERIFICATION:")
    click.echo("-" * 15)
    click.echo("• Run 'python main.py info' to see current authentication status")
    click.echo("• Use 'python main.py --auth-mode auto' to auto-detect authentication method")
    click.echo()
    
    click.echo("❓ NEED HELP?")
    click.echo("-" * 12)
    click.echo("• OAuth2 issues: Make sure Gmail API is enabled and OAuth consent is configured")
    click.echo("• Service Account issues: Verify domain-wide delegation is properly configured")
    click.echo("• Both: Check that JSON files are valid and in the correct directory")
    click.echo("\n" + "=" * 60)


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