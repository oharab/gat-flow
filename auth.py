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
            
            print("🔐 Authentication required for Google Gmail API access")
            print("📋 Required permissions: Gmail settings management")
            print("🌐 Opening browser for Google OAuth2 authentication...")
            print("   - Please sign in with your Google Workspace account")
            print("   - Grant permission to manage Gmail vacation settings")
            print("   - Close the browser tab when authentication is complete")
            print()
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.credentials_file), self.SCOPES
            )
            
            # Force browser authentication with explicit parameters
            self._creds = flow.run_local_server(
                port=0,
                authorization_prompt_message="Please visit this URL to authorize the application: {url}",
                success_message="Authentication successful! You can close this tab.",
                open_browser=True
            )
            
            self._save_token()
            print("✅ Authentication successful! Token saved for future use.")
        
        return self._creds
    
    def _save_token(self) -> None:
        """Save credentials to token file for future use."""
        if self._creds:
            with open(self.token_file, "w") as token:
                token.write(self._creds.to_json())
    
    def force_reauthentication(self) -> Credentials:
        """Force re-authentication by clearing existing credentials.
        
        Returns:
            Fresh Google OAuth2 credentials object
        """
        print("🔄 Forcing re-authentication...")
        
        # Clear existing credentials
        self._creds = None
        if self.token_file.exists():
            os.remove(self.token_file)
            print(f"Removed existing token file: {self.token_file}")
        
        # Re-authenticate
        return self.authenticate()
    
    def revoke_token(self) -> bool:
        """Revoke the current token and delete token file.
        
        Returns:
            True if token was successfully revoked, False otherwise
        """
        if not self._creds:
            print("No active credentials to revoke.")
            return False
        
        try:
            print("🔓 Revoking Google API access token...")
            self._creds.revoke(Request())
            if self.token_file.exists():
                os.remove(self.token_file)
                print(f"Removed token file: {self.token_file}")
            self._creds = None
            print("✅ Token revoked successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to revoke token: {e}")
            return False