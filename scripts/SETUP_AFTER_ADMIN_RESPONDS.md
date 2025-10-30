# Setup Instructions - After Admin Provides Access

## What Giselle Needs to Provide

You sent the request in `REQUEST_FOR_SALESFORCE_ADMIN.md`. When Giselle responds, she'll provide one of these:

### Option A: Connected App (Preferred)
She'll give you:
- **Consumer Key** (long string)
- Confirmation that she uploaded the certificate (`~/Desktop/salesforce-jwt-certificate.crt`)

### Option B: API User Credentials
She'll give you:
- **Username**: `something@pandadoc.com.full`
- **Password**: `********`
- **Security Token**: `abc123...`

---

## Setup Steps

### If She Provides Option A (Connected App + Consumer Key)

1. **Set environment variables:**
```bash
export SF_CONSUMER_KEY="<consumer_key_from_giselle>"
export SF_USERNAME="aaron.nam@pandadoc.com"
export SF_ORG_ALIAS="pandadoc-full-sandbox"
export SF_JWT_KEY_FILE="$HOME/Desktop/Repos/251024-vapi-trialist-PD-2/scripts/salesforce-certs/server.key"
export SF_DEFAULT_OWNER_ID="<admin_user_id_from_giselle>"
export ANALYTICS_S3_BUCKET="<your_s3_bucket_name>"
```

2. **Test authentication:**
```bash
cd ~/Desktop/Repos/251024-vapi-trialist-PD-2/scripts
python sync_to_salesforce.py
```

### If She Provides Option B (Username/Password)

1. **Install dependency:**
```bash
pip install simple-salesforce
```

2. **Set environment variables:**
```bash
export SF_USERNAME="<username_from_giselle>"
export SF_PASSWORD="<password_from_giselle>"
export SF_TOKEN="<security_token_from_giselle>"
export SF_DOMAIN="test"  # for sandbox
export SF_DEFAULT_OWNER_ID="<admin_user_id_from_giselle>"
export ANALYTICS_S3_BUCKET="<your_s3_bucket_name>"
```

3. **Test authentication:**
```bash
cd ~/Desktop/Repos/251024-vapi-trialist-PD-2/scripts
python sync_to_salesforce.py
```

---

## Create Permanent .env File

Once it works, save credentials:

```bash
cd ~/Desktop/Repos/251024-vapi-trialist-PD-2/scripts

# Option A
cat > .env << 'EOF'
SF_CONSUMER_KEY=<consumer_key>
SF_USERNAME=aaron.nam@pandadoc.com
SF_ORG_ALIAS=pandadoc-full-sandbox
SF_JWT_KEY_FILE=./salesforce-certs/server.key
SF_DEFAULT_OWNER_ID=<admin_user_id>
ANALYTICS_S3_BUCKET=<bucket_name>
AWS_REGION=us-west-1
EOF

# OR Option B
cat > .env << 'EOF'
SF_USERNAME=<api_username>
SF_PASSWORD=<password>
SF_TOKEN=<security_token>
SF_DOMAIN=test
SF_DEFAULT_OWNER_ID=<admin_user_id>
ANALYTICS_S3_BUCKET=<bucket_name>
AWS_REGION=us-west-1
EOF
```

---

## Set Up Daily Cron

Once working, schedule daily runs:

### Option 1: GitHub Actions
```yaml
# .github/workflows/salesforce-sync.yml
name: Salesforce Voice AI Sync
on:
  schedule:
    - cron: '0 8 * * *'  # 8am UTC daily
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install boto3
          pip install simple-salesforce  # if using Option B
      - name: Run sync
        run: python scripts/sync_to_salesforce.py
        env:
          SF_USERNAME: ${{ secrets.SF_USERNAME }}
          SF_PASSWORD: ${{ secrets.SF_PASSWORD }}
          SF_TOKEN: ${{ secrets.SF_TOKEN }}
          SF_DOMAIN: ${{ secrets.SF_DOMAIN }}
          SF_DEFAULT_OWNER_ID: ${{ secrets.SF_DEFAULT_OWNER_ID }}
          ANALYTICS_S3_BUCKET: ${{ secrets.ANALYTICS_S3_BUCKET }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: us-west-1
```

### Option 2: AWS Lambda
(Deploy script as Lambda function, trigger with EventBridge daily)

---

## Troubleshooting

### "No Salesforce credentials found"
- Check environment variables are set: `env | grep SF_`

### "ANALYTICS_S3_BUCKET environment variable not set"
- Set: `export ANALYTICS_S3_BUCKET=your-bucket-name`

### "No sessions found for yesterday"
- Normal if no calls happened yesterday
- Or check S3 bucket has data: `aws s3 ls s3://your-bucket/sessions/`

### JWT auth fails
- Verify Consumer Key is correct
- Check certificate was uploaded to Connected App
- Ensure Connected App is approved/active

### Username/password auth fails
- Verify security token is appended to password in some libraries
- Check SF_DOMAIN is "test" for sandbox
- Confirm API access is enabled for the user

---

## Next Steps After Success

1. ✅ Verify Events appear in Salesforce sandbox
2. Update `IMPLEMENTATION_PLAN.md` with actual credentials method used
3. Test with a real call (make test call → wait for session to end → run script next day)
4. Set up automated daily cron
5. Monitor for errors in first week
