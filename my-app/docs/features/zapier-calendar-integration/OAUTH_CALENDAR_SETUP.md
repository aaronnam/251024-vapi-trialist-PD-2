# OAuth2 Calendar Setup (Alternative to Service Account)

If your corporate Google Workspace blocks service accounts, you can use OAuth2 instead.

## Step 1: Create OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google Calendar API
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Configure consent screen:
   - User type: External
   - App name: PandaDoc Voice Agent
   - User support email: your email
   - Developer contact: your email
6. Create OAuth client:
   - Application type: Desktop app
   - Name: PandaDoc Voice Agent
   - Download the credentials JSON

## Step 2: Replace Service Account Code

Replace the `_get_calendar_service` method in `agent.py`:

```python
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import os

def _get_calendar_service(self):
    """Initialize Google Calendar service using OAuth2."""
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None

    # Token file stores the user's access and refresh tokens
    token_file = '.secrets/token.pickle'

    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '.secrets/oauth_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)
```

## Step 3: First-Time Authorization

Run once to authorize:
```bash
uv run python -c "from src.agent import PandaDocTrialistAgent; agent = PandaDocTrialistAgent(); agent._get_calendar_service()"
```

This will open a browser to authorize. After that, it will use the saved token.

## Pros of OAuth2:
- Works with ANY Google account (personal or corporate)
- You control the permissions
- Can create events with attendees and Google Meet links

## Cons of OAuth2:
- Requires manual authorization first time
- Token can expire and need refresh
- Not ideal for production deployment