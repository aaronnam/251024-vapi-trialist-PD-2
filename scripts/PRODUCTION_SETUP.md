# Production Salesforce Setup - Using Test Account

## ✅ Good News: You Can Use Production

Giselle confirmed you can use the production org (which you already have CLI access to) as long as you only create Events for contacts associated with **"Test Stark Industries"** account.

## What You Need from Giselle

1. **Exact Account Name**: Confirm the exact name of the test account:
   - Is it "Test Stark Industries"?
   - Or something else?
   - Account names are case-sensitive in queries

2. **Does the account exist?**: If not, she needs to create it first

3. **Default Owner ID**: Admin User ID to assign Events to when Lead/Contact has no owner

## Setup Steps

### 1. Verify Test Account Exists

```bash
sf data query --query "SELECT Id, Name FROM Account WHERE Name = 'Test Stark Industries'" --target-org PandaDoc-Sandbox
```

If this returns 0 results, ask Giselle to create the account.

### 2. Find an Admin Owner ID

```bash
sf data query --query "SELECT Id, Name FROM User WHERE IsActive = true AND Profile.Name = 'System Administrator' LIMIT 5" --target-org PandaDoc-Sandbox
```

Pick one User ID (format: `005...`) for fallback assignment.

### 3. Set Environment Variables

Create `scripts/.env`:

```bash
# Salesforce - Using existing CLI auth (no password needed!)
SF_ORG_ALIAS=PandaDoc-Sandbox
SF_TEST_ACCOUNT_NAME=Test Stark Industries
SF_DEFAULT_OWNER_ID=005xxxxxxxxxx  # From step 2

# OpenAI - For AI-powered transcript summarization (REQUIRED)
OPENAI_API_KEY=sk-...  # Get from https://platform.openai.com/api-keys

# S3 bucket
ANALYTICS_S3_BUCKET=your-bucket-name
AWS_REGION=us-west-1
```

**Note:** The script uses GPT-5-nano to generate intelligent summaries of call transcripts. Without `OPENAI_API_KEY`, it will fall back to using raw transcripts (truncated to 32K characters).

### 4. Update Script to Use CLI Auth

Since you're using the existing CLI connection, update the script to use CLI method:

```bash
cd ~/Desktop/Repos/251024-vapi-trialist-PD-2/scripts

# The script already supports CLI auth via SF_ORG_ALIAS
# Just make sure SF_ORG_ALIAS is set to your existing org
```

### 5. Test the Script

```bash
# Load environment variables
export SF_ORG_ALIAS=PandaDoc-Sandbox
export SF_TEST_ACCOUNT_NAME="Test Stark Industries"
export SF_DEFAULT_OWNER_ID=005xxxxxxxxxx
export ANALYTICS_S3_BUCKET=your-bucket-name

# Test (will process yesterday's calls)
python sync_to_salesforce.py
```

## How It Works

The script now:
1. ✅ Uses your existing production org connection (`PandaDoc-Sandbox` alias)
2. ✅ **Filters by test account** - only processes Leads/Contacts associated with "Test Stark Industries"
3. ✅ Skips any records not associated with the test account
4. ✅ **AI-powered summarization** - Uses GPT-5-nano to extract qualification signals and key insights
5. ✅ Creates Events only for test account records with intelligent summaries

## Safety Features

- **Lead filter**: `WHERE Company = 'Test Stark Industries'`
- **Contact filter**: `WHERE Account.Name = 'Test Stark Industries'`
- **No credentials needed**: Uses existing CLI session
- **Read-only except Events**: Only creates Event records, doesn't modify Leads/Contacts

## Example Output

```
Processing sessions from: s3://your-bucket/sessions/year=2025/month=01/day=15/
Found 5 session files
⊘ No Lead/Contact found for john@acme.com under 'Test Stark Industries' account
⊘ No Lead/Contact found for jane@bigcorp.com under 'Test Stark Industries' account
✓ Created Event for tony@starkindustries.com (Contact)
✓ Created Event for pepper@starkindustries.com (Lead)
⊘ Skipping session_xyz - no email

==================================================
Sync complete:
  ✓ Success: 2
  ⊘ Skipped: 3
  ✗ Errors:  0
==================================================
```

## Next Steps After Testing

1. Verify Events appear in Salesforce under Test Stark Industries contacts
2. Set up daily cron (GitHub Actions or AWS Lambda)
3. Monitor for first week

## Questions for Giselle

**Message to send:**

> Hi Giselle,
>
> Quick questions about using production for the voice AI sync:
>
> 1. Can you confirm the exact name of the test account? Is it "Test Stark Industries"?
> 2. Does this account exist in production? If not, can you create it?
> 3. What admin User ID should I use for fallback assignment? (need a User ID starting with 005...)
> 4. Should I also add "Voice AI Call" to the Event.Type picklist in production?
>
> Thanks!
