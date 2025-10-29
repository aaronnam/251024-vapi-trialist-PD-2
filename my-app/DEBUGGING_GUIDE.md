# Agent Debugging Guide

## Better Debugging Approaches (from LiveKit Docs)

### 1. Enable DEBUG Log Level

The most important debugging tool - run with detailed logging:

```bash
# Local development
uv run python src/agent.py dev --log-level=DEBUG

# Production logs with DEBUG level
lk agent logs --log-level=DEBUG
```

**Available log levels:**
- `DEBUG`: Detailed information for debugging
- `INFO`: Default level (general information)
- `WARNING`: Warning messages
- `ERROR`: Error messages only
- `CRITICAL`: Critical errors only

### 2. Use LiveKit Cloud Dashboard

Instead of CLI back-and-forth:
- **URL**: https://cloud.livekit.io/projects/p_/agents
- **Provides**:
  - Realtime metrics (session count, agent status)
  - Error tracking and diagnosis
  - Usage and limits
  - Better visualization than CLI

### 3. Stream Logs in Real-Time

```bash
# Stream logs with specific filters
lk agent logs | grep "Error\|TypeError\|received job"

# Watch for specific session
lk agent logs | grep "room_name"
```

### 4. Check Build vs Runtime Logs

```bash
# Runtime logs (default)
lk agent logs

# Build logs (for Docker/deployment issues)
lk agent logs --log-type=build
```

### 5. Add Custom Debug Context

In your agent code (my-app/src/agent.py):

```python
# Add custom fields to logs for better tracking
@session.on("agent_started")
def _on_agent_started(session: VoiceSession):
    ctx.log_fields_context.update({
        "room": ctx.room.name,
        "worker_id": "custom-id",
        "user_email": metadata.get("user_email")
    })
```

### 6. Monitor Specific Events

```python
# Add detailed logging for debugging
@session.on("error")
def _on_error(ev):
    logger.error(f"Session error: {ev.error}", exc_info=True)

@session.on("agent_started")
def _on_started(session):
    logger.info(f"Agent started in room: {ctx.room.name}")

@session.on("agent_stopped")
def _on_stopped(session):
    logger.info(f"Agent stopped after {session.duration}s")
```

### 7. Local Testing with Console Mode

Test agent behavior without frontend:

```bash
# Interactive console testing
uv run python src/agent.py console

# Watch for specific errors
uv run python src/agent.py dev 2>&1 | tee debug.log
```

## Common Issues and Quick Checks

### Agent Not Connecting to Room

1. **Check agent received job request:**
   ```bash
   lk agent logs | grep "received job"
   ```

2. **Check for initialization errors:**
   ```bash
   lk agent logs | grep -A 10 "received job"
   ```

3. **Verify room exists and agent joined:**
   ```bash
   lk agent logs | grep "Participant joined\|connected to room"
   ```

### TTS Not Working

```bash
# Check for TTS errors
lk agent logs | grep -i "tts\|elevenlabs\|TypeError"
```

### Agent Stuck / No Response

1. **Check LLM calls:**
   ```bash
   lk agent logs | grep "LLM\|openai\|completion"
   ```

2. **Check for blocking operations:**
   - Enable DEBUG logs to see timing
   - Look for long delays between events

## Systematic Debug Process

1. **Enable DEBUG logging** (most important!)
2. **Check LiveKit Cloud Dashboard** for high-level view
3. **Stream logs in real-time** during test
4. **Add custom log context** for your specific issue
5. **Test locally** with console mode if possible
6. **Check both build and runtime logs** for deployment issues

## Quick Reference: Useful Log Commands

```bash
# Live tail with timestamp filtering
lk agent logs | grep "$(date +%Y-%m-%d)"

# Count errors
lk agent logs | grep -c "ERROR"

# Find specific room session
lk agent logs | grep "pandadoc_trial_[room-id]"

# Check worker registration
lk agent logs | grep "registered worker\|shutting down"
```
