"""Configuration management for API credentials and default settings."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Configuration handler for the application."""

    def __init__(self, config_file: str | None = None):
        """Initialize configuration.

        Args:
            config_file: Path to .env file (defaults to .env in current directory)
        """
        self.config_file = config_file or ".env"
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from environment file."""
        if Path(self.config_file).exists():
            load_dotenv(self.config_file)

    @property
    def credentials_file(self) -> str:
        """Get OAuth2 credentials file path."""
        return os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

    @property
    def token_file(self) -> str:
        """Get token storage file path."""
        return os.getenv("GOOGLE_TOKEN_FILE", "token.json")

    @property
    def default_subject(self) -> str:
        """Get default vacation response subject."""
        return os.getenv("DEFAULT_VACATION_SUBJECT", "Out of Office")

    @property
    def default_message(self) -> str:
        """Get default vacation response message."""
        return os.getenv(
            "DEFAULT_VACATION_MESSAGE",
            "I am currently out of the office and will return on [DATE]. "
            "For urgent matters, please contact [CONTACT]. "
            "I will respond to your email upon my return.",
        )

    @property
    def default_contacts_only(self) -> bool:
        """Whether to restrict vacation responses to contacts only by default."""
        return os.getenv("DEFAULT_CONTACTS_ONLY", "false").lower() == "true"

    @property
    def default_domain_only(self) -> bool:
        """Whether to restrict vacation responses to same domain only by default."""
        return os.getenv("DEFAULT_DOMAIN_ONLY", "false").lower() == "true"

    def get_message_templates(self) -> dict[str, dict[str, str]]:
        """Get predefined message templates plus any custom templates."""
        templates = {
            "vacation": {
                "subject": "Out of Office - On Vacation",
                "message": (
                    "Thank you for your email. I am currently on vacation and will be "
                    "out of the office from [START_DATE] to [END_DATE].\n\n"
                    "I will have limited access to email during this time and will "
                    "respond to your message upon my return.\n\n"
                    "For urgent matters, please contact [EMERGENCY_CONTACT].\n\n"
                    "Best regards"
                ),
            },
            "sick": {
                "subject": "Out of Office - Medical Leave",
                "message": (
                    "Thank you for your email. I am currently out of the office on "
                    "medical leave and expect to return on [RETURN_DATE].\n\n"
                    "For urgent matters, please contact [EMERGENCY_CONTACT].\n\n"
                    "I will respond to your email upon my return.\n\n"
                    "Best regards"
                ),
            },
            "conference": {
                "subject": "Out of Office - At Conference",
                "message": (
                    "Thank you for your email. I am currently attending [CONFERENCE_NAME] "
                    "from [START_DATE] to [END_DATE].\n\n"
                    "I will have limited access to email during this time. For urgent "
                    "matters, please contact [EMERGENCY_CONTACT].\n\n"
                    "I will respond to your message upon my return.\n\n"
                    "Best regards"
                ),
            },
            "training": {
                "subject": "Out of Office - Training",
                "message": (
                    "Thank you for your email. I am currently attending training and "
                    "will be out of the office from [START_DATE] to [END_DATE].\n\n"
                    "I will respond to your email upon my return. For urgent matters, "
                    "please contact [EMERGENCY_CONTACT].\n\n"
                    "Best regards"
                ),
            },
        }

        # Add custom templates from environment variables.
        # Naming convention for env vars: prefix + uppercase name + suffix,
        # using _SUBJECT and _MESSAGE pairs under the CUSTOM_TEMPLATE_ prefix.
        import re

        for key, value in os.environ.items():
            if key.startswith("CUSTOM_TEMPLATE_") and key.endswith("_SUBJECT"):
                # Extract template name (e.g., CUSTOM_TEMPLATE_REMOTE_SUBJECT -> remote)
                match = re.match(r"CUSTOM_TEMPLATE_(.+)_SUBJECT", key)
                if match:
                    template_name = match.group(1).lower()
                    message_key = f"CUSTOM_TEMPLATE_{match.group(1)}_MESSAGE"
                    message = os.getenv(message_key)

                    if message:  # Only add if both subject and message are defined
                        templates[template_name] = {
                            "subject": value,
                            "message": message,
                        }

        return templates

    def create_sample_env_file(self, file_path: str = ".env.example") -> None:
        """Create a sample environment file with configuration options.

        Args:
            file_path: Path where to create the sample file
        """
        sample_content = """# Google API Configuration
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json

# Default Vacation Message Settings
DEFAULT_VACATION_SUBJECT=Out of Office
DEFAULT_VACATION_MESSAGE=I am currently out of the office and will return on [DATE]. For urgent matters, please contact [CONTACT]. I will respond to your email upon my return.

# Default Restrictions
DEFAULT_CONTACTS_ONLY=false
DEFAULT_DOMAIN_ONLY=false
"""

        with open(file_path, "w") as f:
            f.write(sample_content)

        logger.info("Sample environment file created: %s", file_path)
        logger.info("Copy this to '.env' and customize the values as needed.")
