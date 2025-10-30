# Salesforce API Access Request for Voice AI Integration

## What I Need

API access to the **Full Sandbox** (`pandadoc--full.sandbox.my.salesforce.com`) for an automated script that syncs voice call data to Salesforce.

## Why

We're building a voice AI agent that talks to trial users. After each call, we need to automatically create an Event record on the Lead/Contact's activity timeline so the sales team can see the engagement.

## What the Script Does

1. Reads call data from S3 (email, timestamp, transcript)
2. Queries Salesforce to find the Lead/Contact by email
3. Creates an Event record with:
   - **WhoId**: The Lead/Contact
   - **Type**: "Voice AI Call" (need this added as picklist value)
   - **Assigned To**: The record's owner (or default admin)
   - **Start Time**: When the call happened
   - **Description**: Call transcript

## Technical Requirements

**Option A: Connected App (Preferred for automation)**
1. Enable "App Manager" in Full Sandbox Setup
2. Allow me to create a Connected App with:
   - OAuth enabled
   - JWT/certificate authentication
   - Scopes: `api`, `refresh_token`

**Option B: API User (Simpler alternative)**
1. Create a dedicated integration user (e.g., `voiceai-integration@pandadoc.com.full`)
2. Assign System Administrator or API-only profile
3. Grant API access
4. Provide username, password, and security token
5. User should NOT require SSO (needs password auth)

**Also Need:**
- "Voice AI Call" added to Event.Type picklist values
- A default admin User ID for fallback assignment (when Lead/Contact has no owner)

## Why Sandbox vs Production

Testing the integration safely before deploying to production.

## Questions?

The script runs daily via cron, reads yesterday's calls, and creates Events. No data leaves Salesforce - it only reads Leads/Contacts and creates Events.
