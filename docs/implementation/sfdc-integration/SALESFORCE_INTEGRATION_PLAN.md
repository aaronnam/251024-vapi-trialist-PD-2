# Salesforce Integration: Voice Call to Event Record

## Status: ✅ Ready to Test (Using Production with Test Account Filter)

**Approved by:** Giselle (Salesforce Admin)

**Approach:** Use production org with filter for "Test Stark Industries" account only

**Next step:** Confirm test account name and get admin Owner ID

See `PRODUCTION_SETUP.md` for complete setup instructions.

---

## Goal

When a voice call ends, create a Salesforce Event on the contact/lead's timeline.

## Complete Data Flow

### Step 1: Voice Call Ends (Already Happening)

**Location:** `my-app/src/agent.py:1434-1462`

When call ends, we capture:
```python
session_payload = {
    "user_email": "john@acme.com",           # From pre-call form
    "start_time": "2025-01-15T14:30:00Z",    # When call started
    "transcript_text": "AGENT: Hi...\nUSER: Hello...",
    "duration_seconds": 245.6
}
```

### Step 2: Data Goes to S3 (Already Happening)

**Location:** `my-app/src/utils/analytics_queue.py:78-125`

Stored at: `s3://your-bucket/sessions/year=2025/month=01/day=15/{session_id}.json.gz`

Contains:
```json
{
  "user_email": "john@acme.com",
  "start_time": "2025-01-15T14:30:00Z",
  "transcript_text": "Full conversation transcript...",
  "duration_seconds": 245.6,
  "session_id": "rm_abc123"
}
```

### Step 3: Daily Sync Script (NEW)

**Location:** `scripts/sync_to_salesforce.py` (to be created)

Runs daily at 8am UTC via cron.

**For each session file from yesterday:**

#### 3.1 Query Salesforce for Lead/Contact

```python
email = "john@acme.com"  # From session data

# Try to find Lead first
lead_result = sf.query(f"""
    SELECT Id, OwnerId
    FROM Lead
    WHERE Email = '{email}'
    AND IsConverted = false
""")

# If no Lead, try Contact
if not lead_result['records']:
    contact_result = sf.query(f"""
        SELECT Id, OwnerId
        FROM Contact
        WHERE Email = '{email}'
    """)
```

**Result:** We get either:
- Lead record: `{'Id': '00Q...', 'OwnerId': '005...'}`
- Contact record: `{'Id': '003...', 'OwnerId': '005...'}`
- Nothing (skip this session)

#### 3.2 Create Salesforce Event

```python
# From step 3.1
who_id = '00Q...'  # Lead or Contact ID
owner_id = '005...' or 'default_admin_id'  # Owner or fallback

# From session data
start_time = "2025-01-15T14:30:00Z"
transcript = "AGENT: Hi...\nUSER: Hello..."
duration_minutes = int(245.6 / 60)  # = 4 minutes

# Create the Event
sf.Event.create({
    'WhoId': who_id,              # ← Links to Lead/Contact
    'OwnerId': owner_id,          # ← Assigned To field
    'Type': 'Voice AI Call',      # ← New picklist value Giselle adds
    'Subject': f'Voice AI Call - {start_time[:10]}',  # "Voice AI Call - 2025-01-15"
    'StartDateTime': start_time,  # ← Call timestamp
    'Description': transcript,     # ← Full conversation
    'DurationInMinutes': duration_minutes
})
```

**Result in Salesforce:**

```
Event Record on john@acme.com's timeline:
┌─────────────────────────────────────────┐
│ Subject: Voice AI Call - 2025-01-15     │
│ Type: Voice AI Call                     │
│ Assigned To: Sarah Smith (or admin)     │
│ Start: Jan 15, 2025 2:30 PM             │
│ Duration: 4 minutes                     │
│ Related To: John Doe (Lead/Contact)     │
│ Description:                            │
│   AGENT: Hi there, I'm Sarah...         │
│   USER: Hello...                        │
└─────────────────────────────────────────┘
```

## Field Mapping Table

| Salesforce Event Field | Source | Example Value |
|----------------------|---------|---------------|
| **WhoId** | Query SF by email → get Lead/Contact ID | `00Q5f000001AbcD` |
| **Type** | Hardcoded | `"Voice AI Call"` |
| **OwnerId** (Assigned To) | From Lead/Contact record, or fallback | `005f000000Xyz123` |
| **Subject** | Template with date | `"Voice AI Call - 2025-01-15"` |
| **StartDateTime** | session_data.start_time | `"2025-01-15T14:30:00Z"` |
| **Description** | session_data.transcript_text | Full transcript |
| **DurationInMinutes** | session_data.duration_seconds / 60 | `4` |

## Complete Script

```python
# scripts/sync_to_salesforce.py
import os
import boto3
import gzip
import json
from datetime import datetime, timedelta
from simple_salesforce import Salesforce

def sync_yesterday_calls():
    # Connect to Salesforce
    sf = Salesforce(
        username=os.getenv('SF_USERNAME'),
        password=os.getenv('SF_PASSWORD'),
        security_token=os.getenv('SF_TOKEN'),
        domain='test'  # Use 'test' for sandbox, remove for production
    )

    # Connect to S3
    s3 = boto3.client('s3')
    bucket = os.getenv('ANALYTICS_S3_BUCKET')
    admin_owner_id = os.getenv('SF_DEFAULT_OWNER_ID')  # Fallback owner

    # Get yesterday's date for S3 path
    yesterday = datetime.now() - timedelta(days=1)
    prefix = f"sessions/year={yesterday.year}/month={yesterday.month:02d}/day={yesterday.day:02d}/"

    print(f"Processing sessions from {prefix}")

    # List all session files from yesterday
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    if 'Contents' not in response:
        print("No sessions found for yesterday")
        return

    for obj in response['Contents']:
        # Load session data from S3
        compressed_data = s3.get_object(Bucket=bucket, Key=obj['Key'])['Body'].read()
        session_data = json.loads(gzip.decompress(compressed_data))

        email = session_data.get('user_email')
        if not email:
            print(f"Skipping {obj['Key']} - no email")
            continue

        # Step 1: Find Lead or Contact in Salesforce
        try:
            # Try Lead first (unconverted only)
            lead_query = f"SELECT Id, OwnerId FROM Lead WHERE Email = '{email}' AND IsConverted = false"
            lead_result = sf.query(lead_query)

            if lead_result['records']:
                record = lead_result['records'][0]
                record_type = 'Lead'
            else:
                # Try Contact
                contact_query = f"SELECT Id, OwnerId FROM Contact WHERE Email = '{email}'"
                contact_result = sf.query(contact_query)

                if contact_result['records']:
                    record = contact_result['records'][0]
                    record_type = 'Contact'
                else:
                    print(f"No Lead/Contact found for {email}")
                    continue

            # Step 2: Create Event
            event_data = {
                'WhoId': record['Id'],
                'OwnerId': record.get('OwnerId') or admin_owner_id,
                'Type': 'Voice AI Call',
                'Subject': f"Voice AI Call - {session_data['start_time'][:10]}",
                'StartDateTime': session_data['start_time'],
                'Description': session_data.get('transcript_text', 'No transcript available')[:32000],  # SF limit
                'DurationInMinutes': int(session_data.get('duration_seconds', 0) / 60)
            }

            sf.Event.create(event_data)
            print(f"✓ Created Event for {email} ({record_type})")

        except Exception as e:
            print(f"✗ Failed for {email}: {e}")
            continue

if __name__ == '__main__':
    sync_yesterday_calls()
```

## Setup

### 1. Install Dependencies

```bash
pip install simple-salesforce boto3
```

### 2. Configure Environment Variables

```bash
# Salesforce credentials
SF_USERNAME=your-username@pandadoc.com.sandbox  # Add .sandbox for sandbox
SF_PASSWORD=your-password
SF_TOKEN=your-security-token
SF_DEFAULT_OWNER_ID=005f000000Xyz123  # Admin user ID for fallback

# S3 (already configured)
ANALYTICS_S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-west-1
```

### 3. Test Manually

```bash
# Test with yesterday's data
python scripts/sync_to_salesforce.py
```

### 4. Set Up Daily Cron

**Option A: AWS Lambda + EventBridge**
- Create Lambda function with script above
- EventBridge rule: `cron(0 8 * * ? *)`

**Option B: GitHub Actions**
```yaml
name: Salesforce Sync
on:
  schedule:
    - cron: '0 8 * * *'
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pip install simple-salesforce boto3
      - run: python scripts/sync_to_salesforce.py
    env:
      SF_USERNAME: ${{ secrets.SF_USERNAME }}
      SF_PASSWORD: ${{ secrets.SF_PASSWORD }}
      SF_TOKEN: ${{ secrets.SF_TOKEN }}
      SF_DEFAULT_OWNER_ID: ${{ secrets.SF_DEFAULT_OWNER_ID }}
      ANALYTICS_S3_BUCKET: ${{ secrets.ANALYTICS_S3_BUCKET }}
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

## Testing in Sandbox

1. Make a test call with email matching a sandbox Lead/Contact
2. Wait for session to end (data goes to S3)
3. Run script: `python scripts/sync_to_salesforce.py`
4. Check Salesforce sandbox for Event on the Lead/Contact's Activity timeline

## What Giselle Needs to Do

1. Add "Voice AI Call" as a picklist value for Event.Type field
2. Provide default admin Owner ID for fallback assignment
3. Grant API access to your Salesforce user account (if not already enabled)
