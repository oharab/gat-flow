"""Core Google Gmail API integration for managing vacation settings."""

from datetime import datetime
from typing import Dict, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from auth import BaseAuth


class GmailVacationManager:
    """Manage Gmail vacation responder settings via Google API."""
    
    def __init__(self, auth_handler: BaseAuth, user_email: Optional[str] = None):
        """Initialize Gmail API client.
        
        Args:
            auth_handler: Authentication handler (OAuth2 or Service Account)
            user_email: Email of user to manage (required for service account)
        """
        self.auth_handler = auth_handler
        self.user_email = user_email
        self._service = None
        self._current_user_id = None
    
    @property
    def service(self):
        """Get or create Gmail API service."""
        if not self._service:
            creds = self.auth_handler.authenticate(self.user_email)
            self._service = build("gmail", "v1", credentials=creds)
        return self._service
    
    @property
    def user_id(self) -> str:
        """Get user ID for API calls."""
        if self.user_email:
            return self.user_email
        return "me"
    
    def get_vacation_settings(self) -> Dict:
        """Get current vacation responder settings.
        
        Returns:
            Dictionary containing current vacation settings
            
        Raises:
            HttpError: If API request fails
        """
        try:
            settings = self.service.users().settings().getVacation(userId=self.user_id).execute()
            return settings
        except HttpError as error:
            print(f"An error occurred getting vacation settings: {error}")
            raise
    
    def set_vacation_message(
        self,
        subject: str,
        message: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        contacts_only: bool = False,
        domain_only: bool = False
    ) -> bool:
        """Set vacation responder message.
        
        Args:
            subject: Subject line for vacation response
            message: Body of vacation response message
            start_time: When to start vacation responder (None for immediate)
            end_time: When to end vacation responder (None for manual disable)
            contacts_only: Only send to contacts in circles/address book
            domain_only: Only send to users in same domain
            
        Returns:
            True if vacation message was set successfully, False otherwise
        """
        vacation_settings = {
            "enableAutoReply": True,
            "responseSubject": subject,
            "responseBodyHtml": message,
            "restrictToContacts": contacts_only,
            "restrictToDomain": domain_only,
        }
        
        # Add start time if specified
        if start_time:
            # Convert to milliseconds since epoch
            start_ms = int(start_time.timestamp() * 1000)
            vacation_settings["startTime"] = str(start_ms)
        
        # Add end time if specified
        if end_time:
            # Convert to milliseconds since epoch
            end_ms = int(end_time.timestamp() * 1000)
            vacation_settings["endTime"] = str(end_ms)
        
        try:
            result = self.service.users().settings().updateVacation(
                userId=self.user_id,
                body=vacation_settings
            ).execute()
            
            user_info = f" for {self.user_email}" if self.user_email else ""
            print(f"Vacation message set successfully{user_info}.")
            if start_time:
                print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            if end_time:
                print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
        except HttpError as error:
            print(f"An error occurred setting vacation message: {error}")
            return False
    
    def disable_vacation_message(self) -> bool:
        """Disable vacation responder.
        
        Returns:
            True if vacation responder was disabled successfully, False otherwise
        """
        vacation_settings = {
            "enableAutoReply": False
        }
        
        try:
            self.service.users().settings().updateVacation(
                userId=self.user_id,
                body=vacation_settings
            ).execute()
            
            user_info = f" for {self.user_email}" if self.user_email else ""
            print(f"Vacation message disabled successfully{user_info}.")
            return True
            
        except HttpError as error:
            print(f"An error occurred disabling vacation message: {error}")
            return False
    
    def get_vacation_status(self) -> Dict:
        """Get vacation responder status and details.
        
        Returns:
            Dictionary with vacation status information
        """
        try:
            settings = self.get_vacation_settings()
            
            status = {
                "enabled": settings.get("enableAutoReply", False),
                "subject": settings.get("responseSubject", ""),
                "message": settings.get("responseBodyHtml", ""),
                "contacts_only": settings.get("restrictToContacts", False),
                "domain_only": settings.get("restrictToDomain", False),
            }
            
            # Parse timestamps if present
            if "startTime" in settings:
                start_ms = int(settings["startTime"])
                status["start_time"] = datetime.fromtimestamp(start_ms / 1000)
            
            if "endTime" in settings:
                end_ms = int(settings["endTime"])
                status["end_time"] = datetime.fromtimestamp(end_ms / 1000)
            
            return status
            
        except HttpError as error:
            print(f"An error occurred getting vacation status: {error}")
            return {}
    
    def print_vacation_status(self) -> None:
        """Print formatted vacation responder status."""
        status = self.get_vacation_status()
        
        if not status:
            print("Could not retrieve vacation status.")
            return
        
        user_info = f" for {self.user_email}" if self.user_email else ""
        print(f"\n=== Vacation Responder Status{user_info} ===")
        print(f"Enabled: {'Yes' if status.get('enabled') else 'No'}")
        
        if status.get("enabled"):
            print(f"Subject: {status.get('subject', 'N/A')}")
            print(f"Message: {status.get('message', 'N/A')}")
            print(f"Contacts Only: {'Yes' if status.get('contacts_only') else 'No'}")
            print(f"Domain Only: {'Yes' if status.get('domain_only') else 'No'}")
            
            if "start_time" in status:
                print(f"Start Time: {status['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            if "end_time" in status:
                print(f"End Time: {status['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("================================\n")