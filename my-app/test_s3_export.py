#!/usr/bin/env python3
"""
Test S3 export functionality to diagnose why production calls aren't being saved.
This simulates what happens when a call ends.
"""

import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.analytics_queue import send_to_analytics_queue, upload_to_s3, BOTO3_AVAILABLE, get_s3_client

def test_environment():
    """Check if environment variables are set"""
    print("=" * 60)
    print("ENVIRONMENT VARIABLE CHECK")
    print("=" * 60)

    bucket = os.getenv('ANALYTICS_S3_BUCKET')
    aws_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION')

    print(f"✓ ANALYTICS_S3_BUCKET: {bucket if bucket else '❌ NOT SET'}")
    print(f"✓ AWS_ACCESS_KEY_ID: {'✅ SET' if aws_key else '❌ NOT SET'}")
    print(f"✓ AWS_SECRET_ACCESS_KEY: {'✅ SET' if aws_secret else '❌ NOT SET'}")
    print(f"✓ AWS_REGION: {aws_region if aws_region else '❌ NOT SET (will use us-west-1)'}")
    print(f"✓ boto3 available: {'✅ YES' if BOTO3_AVAILABLE else '❌ NO'}")
    print()

    if not bucket:
        print("⚠️  PROBLEM FOUND: ANALYTICS_S3_BUCKET is not set!")
        print("   This is why sessions aren't being saved to S3.")
        return False

    if not BOTO3_AVAILABLE:
        print("⚠️  PROBLEM FOUND: boto3 is not available!")
        return False

    return True

def test_s3_client():
    """Test if S3 client can be created"""
    print("=" * 60)
    print("S3 CLIENT TEST")
    print("=" * 60)

    try:
        s3 = get_s3_client()
        if s3:
            print("✅ S3 client created successfully")

            # Try to list buckets to verify credentials
            try:
                response = s3.list_buckets()
                print(f"✅ AWS credentials valid - found {len(response['Buckets'])} buckets")
                return True
            except Exception as e:
                print(f"❌ AWS credentials invalid: {e}")
                return False
        else:
            print("❌ S3 client is None")
            return False
    except Exception as e:
        print(f"❌ Failed to create S3 client: {e}")
        return False

def test_s3_upload():
    """Test actual S3 upload"""
    print("=" * 60)
    print("S3 UPLOAD TEST")
    print("=" * 60)

    bucket = os.getenv('ANALYTICS_S3_BUCKET')
    if not bucket:
        print("❌ Cannot test - ANALYTICS_S3_BUCKET not set")
        return False

    # Create test data matching real session structure
    test_data = {
        "session_id": f"test_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "user_email": "diagnostic@test.com",
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "duration_seconds": 120,
        "discovered_signals": {
            "qualification_tier": "test"
        },
        "tool_calls": [],
        "metrics_summary": {},
        "conversation_state": "TEST",
        "transcript": [
            {"role": "user", "content": "This is a diagnostic test"},
            {"role": "assistant", "content": "Testing S3 upload functionality"}
        ],
        "transcript_text": "USER: This is a diagnostic test\nASSISTANT: Testing S3 upload functionality\n"
    }

    print(f"Uploading test data to bucket: {bucket}")
    print(f"Session ID: {test_data['session_id']}")

    try:
        upload_to_s3(bucket, test_data)
        print("✅ Upload completed (check logs for confirmation)")
        print(f"\nTo verify, run:")
        print(f"aws s3 ls s3://{bucket}/sessions/year={datetime.now().year}/month={datetime.now().month:02d}/day={datetime.now().day:02d}/ --region us-west-1")
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_full_flow():
    """Test the complete analytics queue flow"""
    print("=" * 60)
    print("FULL ANALYTICS FLOW TEST")
    print("=" * 60)

    test_data = {
        "session_id": f"test_full_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "user_email": "diagnostic@test.com",
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "duration_seconds": 120,
        "discovered_signals": {
            "qualification_tier": "test"
        },
        "tool_calls": [],
        "metrics_summary": {},
        "conversation_state": "TEST",
        "transcript": [
            {"role": "user", "content": "Full flow test"},
            {"role": "assistant", "content": "Testing complete analytics pipeline"}
        ],
        "transcript_text": "USER: Full flow test\nASSISTANT: Testing complete analytics pipeline\n"
    }

    print("Testing send_to_analytics_queue()...")
    try:
        await send_to_analytics_queue(test_data)
        print("✅ Analytics queue send completed")
        return True
    except Exception as e:
        print(f"❌ Analytics queue send failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("S3 EXPORT DIAGNOSTIC TEST")
    print("=" * 60)
    print()

    # Load environment variables from .env.local if it exists
    env_file = os.path.join(os.path.dirname(__file__), '.env.local')
    if os.path.exists(env_file):
        print(f"Loading environment from {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print()

    # Run tests
    results = []

    # Test 1: Environment variables
    results.append(("Environment Variables", test_environment()))

    # Test 2: S3 Client
    if results[0][1]:  # Only if env vars are OK
        results.append(("S3 Client", test_s3_client()))

    # Test 3: S3 Upload
    if results[-1][1]:  # Only if S3 client is OK
        results.append(("S3 Upload", test_s3_upload()))

    # Test 4: Full Flow
    if results[-1][1]:  # Only if upload is OK
        import asyncio
        result = asyncio.run(test_full_flow())
        results.append(("Full Analytics Flow", result))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n✅ All tests passed! S3 export should be working.")
        print("\nIf production calls still aren't showing up in S3, the issue is likely:")
        print("1. Environment variables not set in LiveKit Cloud (only local)")
        print("2. Sessions not ending properly (no shutdown callback)")
        print("3. Export callback failing silently")
    else:
        print("\n❌ Tests failed. See output above for details.")
        print("\nCommon fixes:")
        print("1. Set ANALYTICS_S3_BUCKET in .env.local")
        print("2. Ensure AWS credentials are valid")
        print("3. Run: lk agent update-secrets --secrets-file .env.local")
        print("4. Run: lk agent restart")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
