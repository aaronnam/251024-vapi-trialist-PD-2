#!/usr/bin/env python3
"""
Salesforce Voice AI Call Sync Script

Syncs voice call data from S3 to Salesforce Events.
Reads yesterday's call data and creates Event records on Lead/Contact timelines.

REQUIRES: Admin to provide either:
- Option A: Connected App Consumer Key (for JWT auth)
- Option B: API user credentials (username/password/token)
"""

import os
import sys
import boto3
import gzip
import json
from datetime import datetime, timedelta

# Check which auth method to use based on available credentials
AUTH_METHOD = None
import subprocess

if os.getenv('SF_ORG_ALIAS'):
    AUTH_METHOD = 'CLI'
    # Use existing CLI authenticated org (no credentials needed!)
elif os.getenv('SF_CONSUMER_KEY'):
    AUTH_METHOD = 'JWT'
    # JWT authentication (requires Connected App)
elif os.getenv('SF_USERNAME') and os.getenv('SF_PASSWORD'):
    AUTH_METHOD = 'PASSWORD'
    # Username/password authentication
    try:
        from simple_salesforce import Salesforce
    except ImportError:
        print("ERROR: simple-salesforce not installed. Run: pip install simple-salesforce")
        sys.exit(1)
else:
    print("ERROR: No Salesforce credentials found!")
    print("\nSet environment variables for one of these methods:")
    print("\nOption A (CLI - Easiest, uses existing sf org login):")
    print("  SF_ORG_ALIAS=PandaDoc-Sandbox")
    print("\nOption B (JWT - requires Connected App):")
    print("  SF_CONSUMER_KEY=<consumer_key>")
    print("  SF_USERNAME=<your_email>")
    print("  SF_ORG_ALIAS=pandadoc-full-sandbox")
    print("\nOption C (Username/Password):")
    print("  SF_USERNAME=<username>")
    print("  SF_PASSWORD=<password>")
    print("  SF_TOKEN=<security_token>")
    print("  SF_DOMAIN=test  # 'test' for sandbox, omit for production")
    sys.exit(1)


def get_salesforce_client():
    """Get authenticated Salesforce client."""
    if AUTH_METHOD == 'CLI':
        # Use existing CLI authenticated org (simplest method)
        org_alias = os.getenv('SF_ORG_ALIAS')
        return org_alias

    elif AUTH_METHOD == 'JWT':
        # Authenticate via CLI using JWT
        org_alias = os.getenv('SF_ORG_ALIAS', 'pandadoc-full-sandbox')
        consumer_key = os.getenv('SF_CONSUMER_KEY')
        username = os.getenv('SF_USERNAME')
        jwt_key_file = os.getenv('SF_JWT_KEY_FILE', './salesforce-certs/server.key')

        # Login via JWT
        result = subprocess.run([
            'sf', 'org', 'login', 'jwt',
            '--client-id', consumer_key,
            '--jwt-key-file', jwt_key_file,
            '--username', username,
            '--instance-url', 'https://test.salesforce.com',
            '--alias', org_alias
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"JWT auth failed: {result.stderr}")
            sys.exit(1)

        return org_alias

    elif AUTH_METHOD == 'PASSWORD':
        # Direct authentication with simple-salesforce
        return Salesforce(
            username=os.getenv('SF_USERNAME'),
            password=os.getenv('SF_PASSWORD'),
            security_token=os.getenv('SF_TOKEN'),
            domain=os.getenv('SF_DOMAIN', 'test')  # 'test' for sandbox
        )


def query_salesforce(query, sf_client):
    """Query Salesforce - handles both CLI and library methods."""
    if AUTH_METHOD in ['CLI', 'JWT']:
        # Query via CLI
        result = subprocess.run([
            'sf', 'data', 'query',
            '--query', query,
            '--target-org', sf_client,
            '--json'
        ], capture_output=True, text=True)

        data = json.loads(result.stdout)
        return data.get('result', {}).get('records', [])

    else:
        # Query via library
        result = sf_client.query(query)
        return result['records']


def create_salesforce_event(event_data, sf_client):
    """Create Event record in Salesforce."""
    if AUTH_METHOD in ['CLI', 'JWT']:
        # Create via CLI
        fields = ' '.join([f"{k}='{v}'" for k, v in event_data.items()])
        result = subprocess.run([
            'sf', 'data', 'create', 'record',
            '--sobject', 'Event',
            '--values', fields,
            '--target-org', sf_client
        ], capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Failed to create Event: {result.stderr}")

    else:
        # Create via library
        sf_client.Event.create(event_data)


def sync_yesterday_calls():
    """Main sync function - reads S3 and creates Salesforce Events."""

    # Get Salesforce client
    print("Authenticating to Salesforce...")
    sf = get_salesforce_client()
    print(f"✓ Authenticated ({AUTH_METHOD} method)")

    # Configuration
    bucket = os.getenv('ANALYTICS_S3_BUCKET')
    if not bucket:
        print("ERROR: ANALYTICS_S3_BUCKET environment variable not set")
        sys.exit(1)

    admin_owner_id = os.getenv('SF_DEFAULT_OWNER_ID')
    if not admin_owner_id:
        print("WARNING: SF_DEFAULT_OWNER_ID not set. Events without owners will fail.")

    # Connect to S3
    print(f"Connecting to S3 bucket: {bucket}")
    s3 = boto3.client('s3')

    # Get yesterday's date for S3 path
    yesterday = datetime.now() - timedelta(days=1)
    prefix = f"sessions/year={yesterday.year}/month={yesterday.month:02d}/day={yesterday.day:02d}/"

    print(f"Processing sessions from: s3://{bucket}/{prefix}")

    # List all session files from yesterday
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    except Exception as e:
        print(f"ERROR: Failed to list S3 objects: {e}")
        sys.exit(1)

    if 'Contents' not in response:
        print("No sessions found for yesterday")
        return

    print(f"Found {len(response['Contents'])} session files")

    # Process each session
    success_count = 0
    skip_count = 0
    error_count = 0

    for obj in response['Contents']:
        try:
            # Load session data from S3
            compressed_data = s3.get_object(Bucket=bucket, Key=obj['Key'])['Body'].read()
            session_data = json.loads(gzip.decompress(compressed_data))

            email = session_data.get('user_email')
            if not email:
                print(f"⊘ Skipping {obj['Key']} - no email")
                skip_count += 1
                continue

            # Step 1: Find Lead or Contact in Salesforce
            # IMPORTANT: Only process records associated with Test Stark Industries account
            test_account_name = os.getenv('SF_TEST_ACCOUNT_NAME', 'Test Stark Industries')

            # Try Lead first (unconverted only, associated with test account)
            lead_query = f"""
                SELECT Id, OwnerId, Company
                FROM Lead
                WHERE Email = '{email}'
                AND IsConverted = false
                AND Company = '{test_account_name}'
            """
            leads = query_salesforce(lead_query, sf)

            if leads:
                record = leads[0]
                record_type = 'Lead'
            else:
                # Try Contact (associated with test account)
                contact_query = f"""
                    SELECT Id, OwnerId, Account.Name
                    FROM Contact
                    WHERE Email = '{email}'
                    AND Account.Name = '{test_account_name}'
                """
                contacts = query_salesforce(contact_query, sf)

                if contacts:
                    record = contacts[0]
                    record_type = 'Contact'
                else:
                    print(f"⊘ No Lead/Contact found for {email} under '{test_account_name}' account")
                    skip_count += 1
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

            create_salesforce_event(event_data, sf)
            print(f"✓ Created Event for {email} ({record_type})")
            success_count += 1

        except Exception as e:
            print(f"✗ Failed for {email}: {e}")
            error_count += 1
            continue

    # Summary
    print("\n" + "="*50)
    print(f"Sync complete:")
    print(f"  ✓ Success: {success_count}")
    print(f"  ⊘ Skipped: {skip_count}")
    print(f"  ✗ Errors:  {error_count}")
    print("="*50)


if __name__ == '__main__':
    sync_yesterday_calls()
