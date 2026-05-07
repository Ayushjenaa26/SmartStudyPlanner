# Google Calendar Integration Setup Guide

This guide shows how to integrate Google Calendar with your Smart Study Planner using Auth0 Token Vault for secure credential storage.

## Prerequisites

- Auth0 account with Token Vault enabled
- Google Cloud Platform (GCP) project
- Python 3.8+

## Step 1: Set Up Google OAuth Credentials

### 1.1 Create a GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown and select **New Project**
3. Enter `SmartStudyPlanner` as the project name
4. Click **Create**

### 1.2 Enable Google Calendar API

1. In the GCP Console, go to **APIs & Services** > **Library**
2. Search for "Google Calendar API"
3. Click on it and select **Enable**

### 1.3 Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Choose **Web application** as the application type
4. Under "Authorized redirect URIs", add:
   - `http://localhost:8000/api/calendar/oauth/callback`
   - `https://yourdomain.com/api/calendar/oauth/callback` (for production)
5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

### 1.4 Download Credentials JSON

1. From the same credentials page, click the download icon next to your OAuth client
2. Save as `credentials.json` in the `backend/` directory

## Step 2: Configure Auth0 Token Vault

### 2.1 Enable Token Vault in Auth0

1. Go to [Auth0 Dashboard](https://manage.auth0.com/)
2. Navigate to **Settings** > **Integrations** > **Token Vault**
3. Enable Token Vault (if not already enabled)
4. Note your **Vault API URL**

### 2.2 Create Machine-to-Machine Application

1. Go to **Applications** > **Applications**
2. Click **+ Create Application**
3. Select **Machine to Machine Applications**
4. Name it `SmartStudyPlanner-API`
5. Authorize the `Auth0 Management API`
6. Grant the following scopes:
   - `read:client_credentials`
   - `create:client_credentials`
   - `update:client_credentials`
   - `delete:client_credentials`

### 2.3 Get M2M Credentials

1. Go to **Applications** > **SmartStudyPlanner-API**
2. Copy the **Client ID** and **Client Secret**
3. These will be used for Token Vault API access

## Step 3: Update Environment Variables

Update your `.env` file with the following:

```env
# Google Calendar OAuth
GOOGLE_CLIENT_ID=your_google_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:8000/api/calendar/oauth/callback

# Auth0 Token Vault
AUTH0_TOKEN_VAULT_API_URL=https://dev-y84psqij4rd2gb3u.us.auth0.com/api/v1/token-vault
AUTH0_TOKEN_VAULT_NAMESPACE=google-calendar

# For Token Vault API access (use M2M credentials)
AUTH0_MANAGEMENT_CLIENT_ID=your_m2m_client_id
AUTH0_MANAGEMENT_CLIENT_SECRET=your_m2m_client_secret
```

## Step 4: Install Dependencies

Run the following command to install required packages:

```bash
pip install -r requirements.txt
```

Required packages:
- `google-auth-oauthlib` - Google OAuth library
- `google-auth-httplib2` - HTTP transport for Google Auth
- `google-api-python-client` - Google API client
- `python-dateutil` - Date parsing utilities
- `httpx` - Async HTTP client for Token Vault API

## Step 5: API Endpoints

### Initiate Google Calendar Authorization

```bash
GET /api/calendar/auth
```

Returns an authorization URL. User visits this URL to grant calendar access.

**Response:**
```json
{
  "status": "success",
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "message": "Visit the URL to authorize Google Calendar access"
}
```

### OAuth Callback (Automatic)

```
GET /api/calendar/oauth/callback?code=...
```

Automatically called by Google after user authorizes. Exchanges code for credentials and stores in Token Vault.

### Sync Tasks to Calendar

```bash
POST /api/calendar/sync
Content-Type: application/json

{
  "plan_id": "optional-plan-id",
  "subject": "optional-subject-filter"
}
```

Syncs pending study tasks to Google Calendar.

**Response:**
```json
{
  "status": "success",
  "message": "Synced 12 tasks to Google Calendar",
  "sync_result": {
    "synced_count": 12,
    "failed_count": 0,
    "synced_tasks": [...],
    "failed_tasks": []
  }
}
```

### List Calendar Events

```bash
GET /api/calendar/events?days=30
```

Lists upcoming events from Google Calendar for the next N days.

### Revoke Google Calendar Access

```bash
POST /api/calendar/revoke
```

Revokes access and removes credentials from Token Vault.

## Step 6: Frontend Integration

Add a button to your dashboard or setup page:

```html
<!-- Connect Google Calendar Button -->
<button id="connectGoogleCalendarBtn" class="btn-primary">
  📅 Connect Google Calendar
</button>

<!-- Sync to Calendar Button (appears after connection) -->
<button id="syncToCalendarBtn" class="btn-secondary" style="display:none;">
  ⬆️ Sync Tasks to Calendar
</button>

<script>
// Connect Google Calendar
document.getElementById('connectGoogleCalendarBtn').addEventListener('click', async () => {
  const response = await authFetch('/api/calendar/auth');
  const data = await response.json();
  if (data.auth_url) {
    window.location.href = data.auth_url;
  }
});

// Sync tasks to calendar
document.getElementById('syncToCalendarBtn').addEventListener('click', async () => {
  const response = await authFetch('/api/calendar/sync', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  const data = await response.json();
  alert(data.message);
});
</script>
```

## Step 7: Testing

1. Start your backend server:
   ```bash
   cd backend
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. Visit your application and click "Connect Google Calendar"

3. Authorize the application at the Google login screen

4. After authorization, you'll be redirected back to your dashboard

5. Click "Sync Tasks to Calendar" to sync your study tasks

## Security Features

- **Auth0 Token Vault**: All Google credentials are stored securely in Auth0's Token Vault, not in your database
- **Encryption**: Credentials are encrypted at rest
- **Scoped Access**: Google API scoped to calendar.googleapis.com only
- **User Isolation**: Each user's credentials are isolated using auth0UserId
- **Token Refresh**: Automatic token refresh handled by google-auth-oauthlib

## Troubleshooting

### "Token Vault API not found"
- Ensure Token Vault is enabled in Auth0
- Check that `AUTH0_TOKEN_VAULT_API_URL` is correct
- Verify M2M credentials have required scopes

### "Google Calendar not connected"
- User hasn't authorized yet
- Call `/api/calendar/auth` endpoint first

### "Failed to sync tasks"
- Check internet connection
- Verify Google API is enabled in GCP
- Check that credentials.json exists in backend/

### Credentials.json not found
- Download from GCP Console
- Place in `backend/` directory
- Ensure filename is exactly `credentials.json`

## Production Deployment

1. Update `GOOGLE_CALENDAR_REDIRECT_URI` to your production domain:
   ```env
   GOOGLE_CALENDAR_REDIRECT_URI=https://yourdomain.com/api/calendar/oauth/callback
   ```

2. Update GCP OAuth credentials with production redirect URI

3. Enable Token Vault in Auth0 (if not already)

4. Use Auth0 Actions to securely manage secrets in production

5. Set up monitoring for Token Vault API calls

## References

- [Google Calendar API Documentation](https://developers.google.com/calendar)
- [Auth0 Token Vault Documentation](https://auth0.com/docs/secure-local-development/token-vault)
- [Google OAuth 2.0 Flow](https://developers.google.com/identity/protocols/oauth2)
