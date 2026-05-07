# Google Calendar Integration - Quick Start

## 📋 Summary

You now have Google Calendar integration with Auth0 Token Vault enabled in your Smart Study Planner. Here's what was added:

### Backend Changes
- **`backend/google_calendar.py`** - Complete Google Calendar integration module with:
  - Auth0 Token Vault client for secure credential storage
  - Google Calendar API manager
  - OAuth flow handling
  - Task-to-calendar event syncing

### Updated Files
- **`requirements.txt`** - Added Google Calendar dependencies
- **`.env`** - Added Google Calendar configuration variables
- **`backend/main.py`** - Added 5 new API endpoints for calendar integration

### New Files
- **`frontend/google-calendar-integration.js`** - UI component for calendar controls
- **`backend/test_google_calendar.py`** - Testing examples
- **`GOOGLE_CALENDAR_SETUP.md`** - Detailed setup guide

## 🚀 Quick Setup (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Google OAuth Credentials
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable "Google Calendar API"
4. Create OAuth 2.0 credentials (Web application)
5. Add redirect URI: `http://localhost:8000/api/calendar/oauth/callback`
6. Download `credentials.json` and save to `backend/`

### 3. Update `.env`
```env
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:8000/api/calendar/oauth/callback

# For Token Vault (Auth0)
AUTH0_TOKEN_VAULT_API_URL=https://dev-y84psqij4rd2gb3u.us.auth0.com/api/v1/token-vault
AUTH0_TOKEN_VAULT_NAMESPACE=google-calendar
```

### 4. Add UI to Dashboard
In `frontend/dashboard.html`, add this in the content area:

```html
<script src="/static/google-calendar-integration.js" defer></script>

<div id="googleCalendarWidget" style="margin-bottom: 20px;"></div>
```

The widget auto-renders based on connection status.

## 📱 How It Works

1. **User clicks "Connect Google Calendar"**
   - Redirected to Google login
   - User authorizes access

2. **OAuth Callback**
   - Exchanged for credentials
   - Stored securely in Auth0 Token Vault
   - User returned to dashboard

3. **User clicks "Sync Tasks"**
   - All pending tasks synced to Google Calendar
   - Each task becomes an all-day event
   - Calendar updated in real-time

## 🔐 Security

- **Encrypted Storage**: Credentials stored in Auth0 Token Vault, not in database
- **User Isolation**: Each user's credentials separate
- **Scoped Access**: Only calendar.googleapis.com scope granted
- **Token Refresh**: Automatic handling of token expiration
- **Revoke Anytime**: User can disconnect with one click

## 📚 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/calendar/auth` | GET | Get authorization URL |
| `/api/calendar/oauth/callback` | GET | Handle OAuth callback (auto) |
| `/api/calendar/sync` | POST | Sync tasks to calendar |
| `/api/calendar/events` | GET | List upcoming events |
| `/api/calendar/revoke` | POST | Disconnect calendar |

## ✅ Testing

Run the test file:
```bash
python backend/test_google_calendar.py
```

Or manually test endpoints:
```bash
# Get auth URL
curl http://localhost:8000/api/calendar/auth \
  -H "Authorization: Bearer YOUR_TOKEN"

# Sync tasks
curl -X POST http://localhost:8000/api/calendar/sync \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"subject": "Physics"}'
```

## 🛠️ Frontend Widget Usage

The `google-calendar-integration.js` file provides a ready-to-use widget that:
- Shows connection status
- Handles authorization flow
- Syncs tasks with visual feedback
- Allows disconnection

### Standalone Usage

```javascript
// Initialize in your page
const calendar = new GoogleCalendarIntegration('containerElementId');

// Or without UI
const calendar = new GoogleCalendarIntegration();
await calendar.authorize();
await calendar.syncTasks({ subject: 'Physics' });
```

## 📊 Data Flow

```
User's Study Tasks (MongoDB)
         ↓
   [/api/calendar/sync]
         ↓
Google Calendar API
         ↓
User's Google Calendar
         ↓
[All devices synced]
```

## 🔄 Workflow Example

1. User creates study plan → Tasks saved in MongoDB
2. User visits dashboard → Sees "Connect Google Calendar" button
3. User clicks button → Redirected to Google OAuth
4. User authorizes → Credentials stored in Auth0 Token Vault
5. User clicks "Sync Tasks" → All pending tasks synced to calendar
6. Tasks appear in Google Calendar → Auto-reminders setup
7. User checks calendar → Integrated study schedule visible

## ⚙️ Configuration Details

**Storage**: Auth0 Token Vault
- Namespace: `google-calendar`
- Key format: `{auth0UserId}_google_creds`
- Encryption: AES-256-GCM (built-in)

**Metadata**: MongoDB `calendar_sync` collection
- Stores: Connection status, sync history, last sync time
- Tracks: Success/failure counts per user

**Scopes**: Google Calendar API
- Read and write calendar events
- No email forwarding access
- No calendar settings access

## 🐛 Troubleshooting

**"Google Calendar not connected"**
- Run authorization flow first
- Check browser console for errors

**"Token Vault API error"**
- Verify Auth0 Token Vault enabled
- Check M2M credentials in Token Vault API calls
- Ensure correct namespace in .env

**Events not syncing**
- Verify Google API enabled in GCP
- Check credentials.json exists in backend/
- Ensure task dates are valid ISO format

## 📖 Full Documentation

See `GOOGLE_CALENDAR_SETUP.md` for:
- Detailed GCP setup
- Auth0 Token Vault configuration
- Advanced API usage
- Production deployment guide
- Security best practices

## 💡 Next Steps

1. ✅ Install packages: `pip install -r requirements.txt`
2. ✅ Set up Google OAuth credentials
3. ✅ Update `.env` file
4. ✅ Add widget to dashboard HTML
5. ✅ Test the integration
6. ✅ Deploy to production

## 🎯 Features

✅ **OAuth 2.0 Flow** - Standard Google authentication  
✅ **Token Management** - Auth0 Token Vault integration  
✅ **Bulk Sync** - Sync all tasks at once  
✅ **Filter Support** - Sync by subject or plan  
✅ **Event Management** - Create, update, delete calendar events  
✅ **Automatic Reminders** - Calendar default reminders enabled  
✅ **User Isolation** - Separate credentials per user  
✅ **Revoke Support** - Easy disconnect with cleanup  

---

**Questions?** See `GOOGLE_CALENDAR_SETUP.md` for detailed documentation.
