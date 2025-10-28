# LiveKit Agent Deployment Checklist

This checklist ensures your agent is properly configured and deployed to LiveKit Cloud.

## Pre-Deployment

### 1. Verify Local Configuration

- [ ] `.env.local` exists with all required secrets
- [ ] Unleash secrets are correctly configured:
  - [ ] `UNLEASH_BASE_URL=https://e-api.unleash.so` (note the "e-" prefix)
  - [ ] `UNLEASH_API_KEY` is set and valid
  - [ ] `UNLEASH_INTERCOM_APP_ID=intercom`
- [ ] Local testing passes: `uv run python src/agent.py console`
- [ ] All tests pass: `uv run pytest`

### 2. Code Quality

- [ ] Code is formatted: `uv run ruff format`
- [ ] No lint errors: `uv run ruff check`
- [ ] Changes are committed to git

## Deployment

### 3. Deploy to LiveKit Cloud

```bash
# Deploy new version
lk agent deploy
```

- [ ] Build completes successfully
- [ ] Deployment succeeds
- [ ] Note the new version number

### 4. Configure Secrets

**CRITICAL**: After deploying, verify all secrets are correctly set in LiveKit Cloud.

```bash
# View current secrets (values hidden)
lk agent secrets
```

- [ ] All required secrets are present
- [ ] `UNLEASH_BASE_URL` is set to `https://e-api.unleash.so` (NOT `https://api.unleash.so`)

**If secrets are missing or incorrect:**

```bash
# Update from .env.local
lk agent update-secrets --secrets-file .env.local

# Or update individual secrets
lk agent update-secrets --secrets "UNLEASH_BASE_URL=https://e-api.unleash.so"

# IMPORTANT: Restart after updating secrets
lk agent restart
```

### 5. Verify Deployment

```bash
# Check agent status
lk agent status
```

- [ ] Status shows "Running"
- [ ] At least 1 replica is active
- [ ] Version matches your deployment

## Post-Deployment Testing

### 6. Verify Unleash Integration

```bash
# Monitor logs during testing
lk agent logs
```

**Create a test session:**
- [ ] Open Agent Playground: https://cloud.livekit.io/projects/p_/agents
- [ ] Create new session
- [ ] Ask: "How do I integrate with Salesforce?"
- [ ] Verify agent searches Unleash successfully

**In logs, verify:**
- [ ] See: `Searching Intercom source (appId: intercom) for query: '...'`
- [ ] NO 404 errors: `Unleash API HTTP error: 404 Not Found`
- [ ] NO 401 errors: `Unleash API HTTP error: 401 Unauthorized`
- [ ] Agent provides detailed answers (not "trouble searching the knowledge base")

### 7. Performance Verification

- [ ] First connection cold start completes within 20 seconds (Build plan)
- [ ] Subsequent responses are quick (<2 seconds)
- [ ] No unexpected errors in logs
- [ ] Session data exports successfully (check for serialization errors)

## Troubleshooting

### Common Issues

**Issue**: Agent shows "trouble searching the knowledge base"
- **Cause**: Unleash secrets incorrect or agent not restarted
- **Fix**:
  1. Check secrets: `lk agent secrets`
  2. Update if wrong: `lk agent update-secrets --secrets "UNLEASH_BASE_URL=https://e-api.unleash.so"`
  3. **Restart**: `lk agent restart`
  4. Test with new session

**Issue**: 404 Not Found errors for `https://api.unleash.so/search`
- **Cause**: `UNLEASH_BASE_URL` missing "e-" prefix
- **Fix**: Update to `https://e-api.unleash.so` and restart

**Issue**: Secrets updated but still seeing errors
- **Cause**: Agent not restarted after secret update
- **Fix**: `lk agent restart` (workers load secrets at startup only)

**Issue**: Old sessions still have errors after fix
- **Cause**: Existing sessions use old worker with old secrets
- **Fix**: Create new session (old sessions won't pick up changes)

## Emergency Rollback

If deployment has critical issues:

```bash
# View previous versions
lk agent versions

# Rollback to previous version
lk agent rollback

# Or rollback to specific version
lk agent rollback --version v20251028230626
```

## Notes

- **Always restart after updating secrets**: `lk agent restart`
- **LiveKit Cloud secrets override code defaults**: Even if your code has correct fallback values, incorrect secrets will override them
- **Cold starts on Build plan**: First connection may take 10-20 seconds
- **Test with new sessions**: After making changes, always create a new session to test
