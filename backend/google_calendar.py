"""
Google Calendar Integration with Auth0 Token Vault
Handles OAuth flow, token management, and calendar sync
"""

import os
import json
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from dateutil.parser import parse as parse_date
from dotenv import load_dotenv

load_dotenv()


class Auth0TokenVault:
    """Manages secure token storage in Auth0 Token Vault"""
    
    def __init__(self):
        self.vault_api_url = os.getenv('AUTH0_TOKEN_VAULT_API_URL')
        self.vault_namespace = os.getenv('AUTH0_TOKEN_VAULT_NAMESPACE', 'google-calendar')
        self.auth0_domain = os.getenv('AUTH0_DOMAIN')
        self.client_id = os.getenv('AUTH0_CLIENT_ID')
        self.issuer = os.getenv('AUTH0_ISSUER')
        
    async def get_management_token(self) -> str:
        """Get Auth0 management API token for Token Vault operations"""
        token_url = f"https://{self.auth0_domain}/oauth/token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                json={
                    "client_id": self.client_id,
                    "client_secret": os.getenv('AUTH0_CLIENT_SECRET'),
                    "audience": f"https://{self.auth0_domain}/api/v1/",
                    "grant_type": "client_credentials"
                }
            )
            response.raise_for_status()
            return response.json()['access_token']
    
    async def store_google_token(self, auth0_user_id: str, google_credentials: Dict) -> bool:
        """Store Google credentials securely in Auth0 Token Vault"""
        try:
            mgmt_token = await self.get_management_token()
            
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {mgmt_token}"}
                
                response = await client.post(
                    f"{self.vault_api_url}/credentials",
                    headers=headers,
                    json={
                        "namespace": self.vault_namespace,
                        "key": f"{auth0_user_id}_google_creds",
                        "secret": json.dumps(google_credentials)
                    }
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error storing Google token in Token Vault: {e}")
            return False
    
    async def retrieve_google_token(self, auth0_user_id: str) -> Optional[Dict]:
        """Retrieve Google credentials from Auth0 Token Vault"""
        try:
            mgmt_token = await self.get_management_token()
            
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {mgmt_token}"}
                
                response = await client.get(
                    f"{self.vault_api_url}/credentials/{self.vault_namespace}/{auth0_user_id}_google_creds",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                return json.loads(data.get('secret', '{}'))
        except Exception as e:
            print(f"Error retrieving Google token from Token Vault: {e}")
            return None
    
    async def delete_google_token(self, auth0_user_id: str) -> bool:
        """Remove Google credentials from Auth0 Token Vault"""
        try:
            mgmt_token = await self.get_management_token()
            
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {mgmt_token}"}
                
                response = await client.delete(
                    f"{self.vault_api_url}/credentials/{self.vault_namespace}/{auth0_user_id}_google_creds",
                    headers=headers
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error deleting Google token from Token Vault: {e}")
            return False


class GoogleCalendarManager:
    """Manages Google Calendar operations"""
    
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_CALENDAR_REDIRECT_URI')
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.vault = Auth0TokenVault()
    
    def get_oauth_flow(self) -> Flow:
        """Create OAuth flow for Google Calendar authorization"""
        return Flow.from_client_secrets_file(
            'credentials.json',  # Download from Google Cloud Console
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
    
    async def get_credentials(self, auth0_user_id: str, authorization_code: Optional[str] = None) -> Optional[Credentials]:
        """
        Get or refresh Google credentials
        If authorization_code provided, exchange for new credentials
        """
        if authorization_code:
            try:
                flow = self.get_oauth_flow()
                credentials = flow.fetch_token(code=authorization_code)
                
                # Store securely in Token Vault
                await self.vault.store_google_token(auth0_user_id, {
                    'token': credentials['access_token'],
                    'refresh_token': credentials.get('refresh_token'),
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'scopes': self.scopes,
                    'expiry': (datetime.utcnow() + timedelta(seconds=credentials['expires_in'])).isoformat()
                })
                
                return Credentials.from_authorized_user_info(credentials)
            except Exception as e:
                print(f"Error exchanging authorization code: {e}")
                return None
        else:
            # Retrieve from Token Vault
            cred_data = await self.vault.retrieve_google_token(auth0_user_id)
            if cred_data:
                return Credentials.from_authorized_user_info(cred_data)
            return None
    
    async def create_calendar_event(
        self, 
        auth0_user_id: str, 
        task_data: Dict
    ) -> Optional[str]:
        """
        Create a calendar event for a study task
        Returns event ID on success
        """
        credentials = await self.get_credentials(auth0_user_id)
        if not credentials:
            return None
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            # Parse task date
            task_date = parse_date(task_data.get('scheduled_date', datetime.now().isoformat()))
            
            event = {
                'summary': f"Study: {task_data.get('task_name', 'Study Session')}",
                'description': f"Subject: {task_data.get('subject', '')}\n{task_data.get('description', '')}",
                'start': {
                    'date': task_date.strftime('%Y-%m-%d'),
                },
                'end': {
                    'date': (task_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                },
                'reminders': {
                    'useDefault': True
                }
            }
            
            created_event = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            return created_event.get('id')
        
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None
    
    async def list_calendar_events(
        self, 
        auth0_user_id: str,
        days_ahead: int = 30
    ) -> List[Dict]:
        """
        List upcoming calendar events from Google Calendar
        """
        credentials = await self.get_credentials(auth0_user_id)
        if not credentials:
            return []
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            now = datetime.utcnow()
            future = now + timedelta(days=days_ahead)
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=future.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        
        except Exception as e:
            print(f"Error listing calendar events: {e}")
            return []
    
    async def update_calendar_event(
        self,
        auth0_user_id: str,
        event_id: str,
        updates: Dict
    ) -> bool:
        """Update an existing calendar event"""
        credentials = await self.get_credentials(auth0_user_id)
        if not credentials:
            return False
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Update event fields
            if 'summary' in updates:
                event['summary'] = updates['summary']
            if 'description' in updates:
                event['description'] = updates['description']
            
            service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            return True
        
        except Exception as e:
            print(f"Error updating calendar event: {e}")
            return False
    
    async def delete_calendar_event(
        self,
        auth0_user_id: str,
        event_id: str
    ) -> bool:
        """Delete a calendar event"""
        credentials = await self.get_credentials(auth0_user_id)
        if not credentials:
            return False
        
        try:
            service = build('calendar', 'v3', credentials=credentials)
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            return True
        
        except Exception as e:
            print(f"Error deleting calendar event: {e}")
            return False
    
    async def sync_tasks_to_calendar(
        self,
        auth0_user_id: str,
        tasks: List[Dict]
    ) -> Dict:
        """
        Sync multiple tasks to Google Calendar
        Returns summary of synced events
        """
        synced = []
        failed = []
        
        for task in tasks:
            event_id = await self.create_calendar_event(auth0_user_id, task)
            if event_id:
                synced.append({
                    'task_id': task.get('id'),
                    'event_id': event_id
                })
            else:
                failed.append(task.get('id'))
        
        return {
            'synced_count': len(synced),
            'failed_count': len(failed),
            'synced_tasks': synced,
            'failed_tasks': failed
        }
    
    async def revoke_access(self, auth0_user_id: str) -> bool:
        """Revoke Google Calendar access and remove stored credentials"""
        return await self.vault.delete_google_token(auth0_user_id)
