# LiveKit Agent Information

## Your Deployed Agent Details

Based on your LiveKit Cloud deployment:

- **Project Name**: `pd-voice-trialist-4`
- **Agent ID**: `CA_9b4oemVRtDEm`
- **LiveKit URL**: `wss://pd-voice-trialist-4-8xjgyb6d.livekit.cloud`
- **Agent Version**: `v20251027182755`
- **Region**: `us-east`
- **Deployed At**: `2025-10-27T18:29:10Z`

## Important Notes

### Agent Name vs Agent ID

In LiveKit Cloud, agents are identified by their **Agent ID** (e.g., `CA_9b4oemVRtDEm`), not by a custom name. This ID is what you need to use in your frontend configuration.

### Getting Your Credentials

To get your API credentials, run:
```bash
lk app env
```

This will display your `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET`.

### Configuration Files to Update

1. **`.env.local`** - Add your LiveKit credentials and agent ID
2. **`app-config.ts`** - Set `agentName: "CA_9b4oemVRtDEm"`

### Quick Setup

```bash
# Get your credentials
lk app env

# Copy the example configuration
cp ../frontend-ui/config/.env.example.filled .env.local

# Edit .env.local and add your API_KEY and API_SECRET
# The AGENT_NAME is already set to CA_9b4oemVRtDEm
```

### Verifying Your Agent

To verify your agent is deployed and running:
```bash
# List deployed agents
lk agent list

# Check agent logs
lk agent logs

# Test in the playground
# Visit: https://cloud.livekit.io/projects/p_/agents
```