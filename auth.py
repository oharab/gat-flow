"""Google authentication handling supporting both OAuth2 and Service Account flows."""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class BaseAuth(ABC):
    """Abstract base class for authentication handlers."""
    
    SCOPES = ["https://www.googleapis.com/auth/gmail.settings.basic"]
    
    @abstractmethod
    def authenticate(self, user_email: Optional[str] = None) -> Union[Credentials, ServiceAccountCredentials]:
        """Authenticate and return valid credentials."""
        pass
    
    @abstractmethod
    def revoke_token(self) -> bool:
        """Revoke the current token."""
        pass


class OAuth2Auth(BaseAuth):
    """Handle Google OAuth2 authentication for personal/individual accounts."""
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        """Initialize OAuth2 authentication handler.
        
        Args:
            credentials_file: Path to OAuth2 client credentials JSON file
            token_file: Path to store/load refresh tokens
        """
        self.credentials_file = Path(credentials_file)
        self.token_file = Path(token_file)
        self._creds: Optional[Credentials] = None
    
    def authenticate(self, user_email: Optional[str] = None) -> Credentials:
        """Authenticate and return valid credentials.
        
        Args:
            user_email: Ignored for OAuth2 (authenticates as the logged-in user)
            
        Returns:
            Google OAuth2 credentials object
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if user_email:
            print("⚠️  OAuth2 mode: user_email parameter ignored (authenticates as logged-in user)")
        
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
                raise AuthenticationError(
                    f"OAuth2 credentials file '{self.credentials_file}' not found. "
                    "Please download it from Google Cloud Console."
                )
            
            print("🔐 OAuth2 Authentication required for Google Gmail API access")
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
            print("✅ OAuth2 authentication successful! Token saved for future use.")
        
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
        print("🔄 Forcing OAuth2 re-authentication...")
        
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
            print("No active OAuth2 credentials to revoke.")
            return False
        
        try:
            print("🔓 Revoking Google OAuth2 access token...")
            self._creds.revoke(Request())
            if self.token_file.exists():
                os.remove(self.token_file)
                print(f"Removed token file: {self.token_file}")
            self._creds = None
            print("✅ OAuth2 token revoked successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to revoke OAuth2 token: {e}")
            return False


class ServiceAccountAuth(BaseAuth):
    """Handle Google Service Account authentication for domain-wide delegation."""
    
    def __init__(self, service_account_file: str = "service-account-key.json"):
        """Initialize Service Account authentication handler.
        
        Args:
            service_account_file: Path to service account JSON key file
        """
        self.service_account_file = Path(service_account_file)
        self._base_creds: Optional[ServiceAccountCredentials] = None
        self._delegated_creds: Optional[ServiceAccountCredentials] = None
        self._current_user_email: Optional[str] = None
    
    def authenticate(self, user_email: Optional[str] = None) -> ServiceAccountCredentials:
        """Authenticate using service account with optional user impersonation.
        
        Args:
            user_email: Email of user to impersonate (required for service account)
            
        Returns:
            Service account credentials (potentially delegated)
            
        Raises:
            AuthenticationError: If authentication fails
        """
        if not self.service_account_file.exists():
            raise AuthenticationError(
                f"Service account key file '{self.service_account_file}' not found. "
                "Please download it from Google Cloud Console."
            )
        
        # Load base service account credentials if not already loaded
        if not self._base_creds:
            print("🔐 Loading service account credentials...")
            try:
                self._base_creds = ServiceAccountCredentials.from_service_account_file(
                    str(self.service_account_file),
                    scopes=self.SCOPES
                )
                print("✅ Service account credentials loaded successfully!")
            except Exception as e:
                raise AuthenticationError(f"Failed to load service account credentials: {e}")
        
        # If no user email specified, return base credentials
        if not user_email:
            print("ℹ️  Using service account credentials without impersonation")
            return self._base_creds
        
        # If same user as before, return cached delegated credentials
        if (self._delegated_creds and 
            self._current_user_email == user_email and 
            self._delegated_creds.valid):
            return self._delegated_creds
        
        # Create delegated credentials for the specified user
        print(f"👤 Impersonating user: {user_email}")
        try:
            self._delegated_creds = self._base_creds.with_subject(user_email)
            self._current_user_email = user_email
            
            # Test the credentials by refreshing them
            self._delegated_creds.refresh(Request())
            print("✅ User impersonation successful!")
            
            return self._delegated_creds
            
        except Exception as e:
            raise AuthenticationError(
                f"Failed to impersonate user '{user_email}': {e}\n"
                "Make sure:\n"
                "1. Domain-wide delegation is enabled for this service account\n"
                "2. The service account has the required OAuth scopes\n"
                "3. The user email is valid and in your domain"
            )
    
    def revoke_token(self) -> bool:
        """Service account tokens cannot be revoked like OAuth2 tokens.
        
        Returns:
            False (service account tokens are not revokable)
        """
        print("ℹ️  Service account credentials cannot be revoked.")
        print("   To disable access, remove the service account key file or")
        print("   disable domain-wide delegation in Google Workspace Admin Console.")
        return False


class AuthManager:
    """Factory class to create appropriate authentication handlers."""
    
    @staticmethod
    def create_oauth2_auth(credentials_file: str = "credentials.json", 
                          token_file: str = "token.json") -> OAuth2Auth:
        """Create OAuth2 authentication handler."""
        return OAuth2Auth(credentials_file, token_file)
    
    @staticmethod
    def create_service_account_auth(service_account_file: str = "service-account-key.json") -> ServiceAccountAuth:
        """Create Service Account authentication handler."""
        return ServiceAccountAuth(service_account_file)
    
    @staticmethod
    def auto_detect_auth_type(oauth2_file: str = "credentials.json",
                             service_account_file: str = "service-account-key.json") -> BaseAuth:
        """Auto-detect authentication type based on available files.
        
        Returns:
            Appropriate authentication handler
            
        Raises:
            AuthenticationError: If no valid credentials files found
        """
        oauth2_path = Path(oauth2_file)
        sa_path = Path(service_account_file)
        
        if sa_path.exists():
            print(f"🔍 Detected service account file: {service_account_file}")
            return AuthManager.create_service_account_auth(service_account_file)
        elif oauth2_path.exists():
            print(f"🔍 Detected OAuth2 credentials file: {oauth2_file}")
            return AuthManager.create_oauth2_auth(oauth2_file)
        else:
            raise AuthenticationError(
                f"No authentication files found. Please provide either:\n"
                f"- OAuth2 credentials: {oauth2_file}\n"
                f"- Service account key: {service_account_file}"
            )