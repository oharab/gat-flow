"""Google OAuth2 authentication handling and token management."""

import json
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class GoogleAuth:
    """Handle Google OAuth2 authentication for Gmail API."""
    
    SCOPES = ["https://www.googleapis.com/auth/gmail.settings.basic"]
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        """Initialize authentication handler.
        
        Args:
            credentials_file: Path to OAuth2 client credentials JSON file
            token_file: Path to store/load refresh tokens
        """
        self.credentials_file = Path(credentials_file)
        self.token_file = Path(token_file)
        self._creds: Optional[Credentials] = None
    
    def authenticate(self) -> Credentials:
        """Authenticate and return valid credentials.
        
        Returns:
            Google OAuth2 credentials object
            
        Raises:
            FileNotFoundError: If credentials file is not found
            Exception: If authentication fails
        """
        if self._creds and self._creds.valid:
            return self._creds
        
        # Load existing token if available
        if self.token_file.exists():
            self._creds = Credentials.from_authorized_user_file(str(self.token_file), self.SCOPES)
        
        # Refresh token if expired but refresh token exists
        if self._creds and self._creds.expired and self._creds.refresh_token:
            try:
                self._creds.refresh(Request())
                self._save_token()
                return self._creds
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                # Fall through to re-authenticate
        
        # Perform OAuth2 flow if no valid credentials
        if not self._creds or not self._creds.valid:
            if not self.credentials_file.exists():
                raise FileNotFoundError(
                    f"Credentials file '{self.credentials_file}' not found. "
                    "Please download it from Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_file), self.SCOPES
            )
            self._creds = flow.run_local_server(port=0)
            self._save_token()
        
        return self._creds
    
    def _save_token(self) -> None:
        """Save credentials to token file for future use."""
        if self._creds:
            with open(self.token_file, "w") as token:
                token.write(self._creds.to_json())
    
    def revoke_token(self) -> bool:
        """Revoke the current token and delete token file.
        
        Returns:
            True if token was successfully revoked, False otherwise
        """
        if not self._creds:
            return False
        
        try:
            self._creds.revoke(Request())
            if self.token_file.exists():
                os.remove(self.token_file)
            self._creds = None
            return True
        except Exception as e:
            print(f"Failed to revoke token: {e}")
            return False