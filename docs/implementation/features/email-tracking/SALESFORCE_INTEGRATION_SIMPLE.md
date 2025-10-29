# Voice AI → Salesforce Integration (Simple Approach)

**To**: PandaDoc Salesforce Team
**Date**: 2025-10-29
**Goal**: Sales sees voice agent calls in Salesforce

---

## The Problem

Voice agent calls happen. Sales teams don't see them in Salesforce.

**Current flow**:
```
User calls agent → Session data exported to S3 → (stops here)
```

**Desired flow**:
```
User calls agent → Session data exported to S3 → Salesforce Task created
```

---

## Recommended Solution: Daily Sync Script

### What It Does

Once per day, reads yesterday's call data from S3 and creates Salesforce Tasks.

**No Lambda. No infrastructure. Just a Python script.**

### The Code

```python
#!/usr/bin/env python3
"""
Daily sync: S3 voice agent sessions → Salesforce Tasks
Run via cron: 0 2 * * * /usr/bin/python3 /path/to/salesforce_sync.py
"""

import boto3
import json
import gzip
from simple_salesforce import Salesforce
from datetime import datetime, timedelta
import os

# Salesforce connection
sf = Salesforce(
    username=os.getenv('SF_USERNAME'),
    password=os.getenv('SF_PASSWORD'),
    security_token=os.getenv('SF_SECURITY_TOKEN')
)

# S3 connection
s3 = boto3.client('s3', region_name='us-west-1')
BUCKET = 'pandadoc-voice-analytics-1761683081'

# Get yesterday's date
yesterday = datetime.now() - timedelta(days=1)
prefix = f"sessions/year={yesterday.year}/month={yesterday.month:02d}/day={yesterday.day:02d}/"

print(f"Syncing calls from {yesterday.date()}...")

# Process each session file
response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
files = response.get('Contents', [])

synced = 0
skipped = 0

for obj in files:
    # Download and decompress
    file_obj = s3.get_object(Bucket=BUCKET, Key=obj['Key'])
    data = json.loads(gzip.decompress(file_obj['Body'].read()))

    # Skip if no email
    email = data.get('user_email')
    if not email:
        print(f"  Skipped (no email): {data.get('session_id')}")
        skipped += 1
        continue

    # Find Contact or Lead in Salesforce
    contact_query = f"SELECT Id, AccountId FROM Contact WHERE Email = '{email}' LIMIT 1"
    contact_result = sf.query(contact_query)

    if contact_result['totalSize'] == 0:
        # Try Lead if no Contact
        lead_query = f"SELECT Id FROM Lead WHERE Email = '{email}' AND IsConverted = false LIMIT 1"
        lead_result = sf.query(lead_query)

        if lead_result['totalSize'] == 0:
            print(f"  Skipped (no SF match): {email}")
            skipped += 1
            continue

        sf_id = lead_result['records'][0]['Id']
    else:
        sf_id = contact_result['records'][0]['Id']

    # Build call summary
    duration_min = int(data['duration_seconds'] / 60)
    tool_calls = data.get('tool_calls', [])

    description_parts = [
        f"Voice AI Call Summary",
        f"Duration: {duration_min} minutes",
        f"Session ID: {data['session_id']}",
        ""
    ]

    # Add discovered signals if present
    signals = data.get('discovered_signals', {})
    if signals:
        description_parts.append("Discovered Information:")
        if signals.get('use_case'):
            description_parts.append(f"• Use Case: {signals['use_case']}")
        if signals.get('team_size'):
            description_parts.append(f"• Team Size: {signals['team_size']}")
        if signals.get('pain_points'):
            description_parts.append(f"• Pain Points: {', '.join(signals['pain_points'])}")
        description_parts.append("")

    # Add tool actions
    if tool_calls:
        description_parts.append("Agent Actions:")
        for call in tool_calls:
            if call['tool'] == 'book_sales_meeting':
                date = call.get('preferred_date', 'TBD')
                description_parts.append(f"✓ Booked sales meeting for {date}")
            elif call['tool'] == 'send_documentation':
                description_parts.append(f"✓ Sent product documentation")
            else:
                description_parts.append(f"✓ {call['tool']}")

    description = "\n".join(description_parts)

    # Check if Task already exists (prevent duplicates)
    existing_task = sf.query(f"SELECT Id FROM Task WHERE Description LIKE '%{data['session_id']}%' LIMIT 1")
    if existing_task['totalSize'] > 0:
        print(f"  Skipped (duplicate): {email}")
        skipped += 1
        continue

    # Create Task
    task = {
        'Subject': f"Voice AI Call - {data['start_time'][:10]}",
        'WhoId': sf_id,
        'ActivityDate': data['start_time'][:10],
        'Status': 'Completed',
        'TaskSubtype': 'Call',
        'Description': description,
        'CallDurationInSeconds': int(data['duration_seconds'])
    }

    try:
        result = sf.Task.create(task)
        print(f"  ✓ Created Task for {email} (ID: {result['id']})")
        synced += 1
    except Exception as e:
        print(f"  ✗ Failed for {email}: {str(e)}")

print(f"\nComplete: {synced} tasks created, {skipped} skipped")
```

### Setup

**1. Install dependencies** (on any existing server):
```bash
pip install simple-salesforce boto3
```

**2. Set environment variables**:
```bash
export SF_USERNAME="integration-user@pandadoc.com"
export SF_PASSWORD="your-password"
export SF_SECURITY_TOKEN="your-token"
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
```

**3. Add to cron** (runs daily at 2 AM):
```bash
crontab -e
# Add this line:
0 2 * * * /usr/bin/python3 /path/to/salesforce_sync.py >> /var/log/sf_sync.log 2>&1
```

**Total setup time**: 1 hour

---

## What Sales Teams See

### In Salesforce

**Task Record**:
- **Subject**: Voice AI Call - 2025-10-29
- **Related To**: John Doe (Contact)
- **Status**: Completed
- **Date**: 2025-10-29
- **Duration**: 15 minutes
- **Description**:
  ```
  Voice AI Call Summary
  Duration: 15 minutes
  Session ID: rm_abc123xyz

  Discovered Information:
  • Use Case: sales_proposals
  • Team Size: 10-50
  • Pain Points: manual contract creation, slow approval process

  Agent Actions:
  ✓ Booked sales meeting for 2025-11-01
  ✓ Sent product documentation
  ```

**Shows up in**:
- Contact Activity Timeline
- Contact Tasks & Events related list
- Reports (Tasks created yesterday, etc.)
- List Views (My Tasks, All Tasks, etc.)

---

## Testing

### Test with Sample Data

```bash
# Create test file in S3
aws s3 cp test_session.json.gz s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=28/ --region us-west-1

# Run sync script
python salesforce_sync.py

# Check Salesforce for new Task
```

### Verify in Salesforce

1. Go to Contact with matching email
2. Check "Activity" tab
3. Look for Task created today with yesterday's date
4. Verify description contains call summary

---

## Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| No email in session | Skip (log message) |
| Email not in Salesforce | Skip (log message) |
| Duplicate Task | Skip (checks session_id in description) |
| Multiple calls same day | Creates separate Task for each |
| Salesforce API error | Log error, continue to next |

---

## Limitations (and Why They're OK)

### 24-hour delay
**Limitation**: Tasks appear next day, not real-time
**Why it's OK**: Sales teams review calls during morning routine, not immediately

### No custom fields
**Limitation**: Can't filter by "voice AI engagement score"
**Why it's OK**: Can filter Tasks by "Voice AI Call" in subject

### No retry logic
**Limitation**: If script fails, manual re-run needed
**Why it's OK**: Cron runs daily, can re-run manually if needed

### Basic error handling
**Limitation**: Errors logged to file, no alerts
**Why it's OK**: Check log once per week, errors are rare

---

## When to Upgrade

### Upgrade to Lambda if:
- Sales says "24-hour delay is too long"
- You need < 1 hour latency
- Call volume > 1000/day

### Add custom fields if:
- Sales requests specific reports (e.g., "calls by use case")
- You have 3+ specific field requests
- Fields will be used in workflows or automations

### Add monitoring if:
- Script fails > 1 time per month
- You have > 50 sync errors per week
- You need SLA guarantees

---

## Salesforce Requirements

### Needed Today

1. **Integration user** with API access
2. **Standard Task object** (already exists)
3. **Contacts have valid emails** (already true)

### NOT Needed

- ❌ Custom fields
- ❌ Custom objects
- ❌ Workflow rules
- ❌ Triggers
- ❌ Apex code
- ❌ Connected app
- ❌ OAuth setup

---

## Cost

| Item | Cost |
|------|------|
| Script runtime | $0 (existing server) |
| S3 API calls | $0 (within free tier) |
| Salesforce API calls | $0 (within limits) |
| **Total** | **$0/month** |

---

## Timeline

| Day | Task | Owner |
|-----|------|-------|
| Day 1 | Get SF credentials, test script locally | Engineering |
| Day 2 | Deploy to server, add to cron, monitor | Engineering |
| Day 3+ | Review with sales team after 1 week | Sales + Engineering |

**Production ready**: 2 days

---

## Validation Plan

### Week 1: Monitor Basic Metrics

- How many Tasks created per day?
- How many emails not found in Salesforce?
- Any errors in log?

### Week 2: Get Sales Feedback

**Questions to ask**:
1. Is 24-hour delay acceptable?
2. What's missing from Task description?
3. What reports do you need?
4. What fields should we add?

### Week 3: Iterate Based on Evidence

- If sales needs real-time → upgrade to Lambda
- If sales needs custom reporting → add requested fields
- If errors are common → add better error handling

---

## Success Criteria

- [ ] Script runs without errors for 7 days
- [ ] 80%+ of calls create Salesforce Tasks
- [ ] Sales team can see call activity in Contact timeline
- [ ] No duplicate Tasks created
- [ ] Errors logged and reviewable

---

## FAQ

**Q: Why not use Lambda for real-time?**
A: Start simple. Add Lambda if sales proves they need real-time. Most don't.

**Q: Why no custom fields?**
A: Don't know what fields sales needs yet. Add after they request them.

**Q: What if we scale to 10k calls/day?**
A: Script handles this fine. If it doesn't, upgrade then (not now).

**Q: What about error monitoring?**
A: Check logs weekly. Add monitoring if errors become frequent.

**Q: How do we prevent duplicates?**
A: Check if Task with session_id already exists before creating.

---

## Next Steps

1. **Engineering**: Set up script on existing server (1 hour)
2. **Salesforce**: Provide integration user credentials (30 min)
3. **Both**: Test with sample data (30 min)
4. **Both**: Enable cron, monitor for 1 week
5. **Both**: Review with sales team, iterate based on feedback

---

## Appendix: Sample Session Data

What's available in S3 files:

```json
{
  "session_id": "rm_abc123xyz",
  "user_email": "john.doe@acme.com",
  "user_metadata": {
    "user_email": "john.doe@acme.com",
    "session_start": "2025-10-29T14:30:00.000Z"
  },
  "start_time": "2025-10-29T14:30:00Z",
  "end_time": "2025-10-29T14:45:00Z",
  "duration_seconds": 900,
  "tool_calls": [
    {
      "tool": "book_sales_meeting",
      "timestamp": "2025-10-29T14:35:00Z",
      "customer_name": "John Doe",
      "customer_email": "john.doe@acme.com",
      "preferred_date": "2025-11-01",
      "preferred_time": "2:00 PM EST",
      "meeting_booked": true,
      "email_source": "stored"
    }
  ],
  "discovered_signals": {
    "use_case": "sales_proposals",
    "team_size": "10-50",
    "pain_points": [
      "manual contract creation",
      "slow approval process"
    ],
    "integration_interest": ["salesforce", "docusign"],
    "timeline": "evaluating now"
  },
  "metrics_summary": {
    "total_llm_calls": 25,
    "total_stt_duration": 450.5,
    "total_tts_duration": 380.2
  }
}
```

All of this is available to include in Task descriptions or (later) populate custom fields.

---

**Philosophy**: Start simple. Add complexity when sales proves they need it. Evidence over assumptions.
