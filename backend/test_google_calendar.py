"""
Google Calendar Integration Test Examples
Demonstrates how to use the Google Calendar sync functionality
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta


class SmartStudyPlannerClient:
    """Client for testing Google Calendar integration"""
    
    def __init__(self, base_url="http://localhost:8000", auth_token=None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def get_auth_url(self) -> str:
        """Get Google Calendar authorization URL"""
        response = await self.client.get(
            f"{self.base_url}/api/calendar/auth",
            headers=self._headers()
        )
        data = response.json()
        return data.get("auth_url")
    
    async def sync_tasks_to_calendar(self, plan_id=None, subject=None) -> dict:
        """Sync tasks to Google Calendar"""
        payload = {}
        if plan_id:
            payload["plan_id"] = plan_id
        if subject:
            payload["subject"] = subject
        
        response = await self.client.post(
            f"{self.base_url}/api/calendar/sync",
            json=payload,
            headers=self._headers()
        )
        return response.json()
    
    async def list_calendar_events(self, days=30) -> dict:
        """List upcoming calendar events"""
        response = await self.client.get(
            f"{self.base_url}/api/calendar/events?days={days}",
            headers=self._headers()
        )
        return response.json()
    
    async def revoke_calendar_access(self) -> dict:
        """Revoke Google Calendar access"""
        response = await self.client.post(
            f"{self.base_url}/api/calendar/revoke",
            headers=self._headers()
        )
        return response.json()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# ============== Test Examples ==============

async def test_get_authorization_url():
    """Test: Get Google Calendar authorization URL"""
    print("\n[TEST 1] Getting Google Calendar authorization URL...")
    
    client = SmartStudyPlannerClient()
    try:
        auth_url = await client.get_auth_url()
        print(f"✓ Authorization URL: {auth_url[:80]}...")
        print("  Visit this URL in your browser to authorize access")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await client.close()


async def test_sync_all_tasks():
    """Test: Sync all pending tasks to calendar"""
    print("\n[TEST 2] Syncing all pending tasks to Google Calendar...")
    
    client = SmartStudyPlannerClient()
    try:
        result = await client.sync_tasks_to_calendar()
        print(f"✓ Sync result:")
        print(f"  - Synced: {result.get('sync_result', {}).get('synced_count')} tasks")
        print(f"  - Failed: {result.get('sync_result', {}).get('failed_count')} tasks")
        print(f"  - Message: {result.get('message')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await client.close()


async def test_sync_by_subject():
    """Test: Sync tasks for a specific subject"""
    print("\n[TEST 3] Syncing Physics tasks to calendar...")
    
    client = SmartStudyPlannerClient()
    try:
        result = await client.sync_tasks_to_calendar(subject="Physics")
        print(f"✓ Synced Physics tasks:")
        print(f"  - Count: {result.get('sync_result', {}).get('synced_count')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await client.close()


async def test_list_events():
    """Test: List upcoming calendar events"""
    print("\n[TEST 4] Listing upcoming calendar events...")
    
    client = SmartStudyPlannerClient()
    try:
        result = await client.list_calendar_events(days=30)
        events = result.get("events", [])
        print(f"✓ Found {len(events)} upcoming events:")
        for event in events[:5]:  # Show first 5
            print(f"  - {event.get('summary')} on {event.get('start', {}).get('date')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await client.close()


async def test_revoke_access():
    """Test: Revoke Google Calendar access"""
    print("\n[TEST 5] Revoking Google Calendar access...")
    
    client = SmartStudyPlannerClient()
    try:
        result = await client.revoke_calendar_access()
        print(f"✓ {result.get('message')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await client.close()


async def run_all_tests():
    """Run all test cases"""
    print("=" * 60)
    print("Smart Study Planner - Google Calendar Integration Tests")
    print("=" * 60)
    
    # Note: Set auth_token from your Auth0 login
    await test_get_authorization_url()
    await test_sync_all_tasks()
    await test_sync_by_subject()
    await test_list_events()
    await test_revoke_access()
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
