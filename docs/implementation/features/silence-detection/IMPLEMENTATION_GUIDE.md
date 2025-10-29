# Integrating Silence Detection & Rate Limiting

## Quick Integration (Add to `my-app/src/agent.py`)

Add these changes to your existing `entrypoint` function (around line 1107):

```python
# Import at the top of agent.py
from silence_timeout import SilenceTimeoutManager

# In your entrypoint function, after creating AgentSession (line ~1107):
async def entrypoint(ctx: JobContext):
    # ... existing code ...

    # Create the agent session (existing code)
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-2",
            language="en",
        ),
        llm=openai.LLM(
            model="gpt-4.1-mini",
            temperature=0.7,
        ),
        tts=elevenlabs.TTS(
            voice="21m00Tcm4TlvDq8ikWAM",
            model="eleven_turbo_v2_5",
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
        # ADD THIS: Configure user away detection
        user_away_timeout=15,  # Mark user as "away" after 15s of no response
    )

    # Create agent instance
    agent = PandaDocTrialistAgent()

    # ADD THIS: Initialize silence timeout manager
    silence_manager = SilenceTimeoutManager(
        session=session,
        ctx=ctx,
        silence_timeout_seconds=30,      # Disconnect after 30s silence
        warning_before_disconnect=10,     # Warn at 20s
    )

    # ADD THIS: Periodic session limit checking
    async def check_limits_periodically():
        """Check time/cost limits every 30 seconds."""
        while True:
            await asyncio.sleep(30)

            # Check session duration (30 min max)
            duration = (datetime.now() - datetime.fromisoformat(agent.session_data["start_time"])).total_seconds()
            if duration > 1800:  # 30 minutes
                logger.warning(f"Session exceeded 30 min limit: {duration/60:.1f} minutes")
                await session.say("We've reached our 30-minute session limit. Please call back if you need more help!")
                await asyncio.sleep(2)
                await session.aclose()
                break

            # Check session cost ($5 max per session)
            if agent.session_costs["total_estimated_cost"] > 5.0:
                logger.warning(f"Session exceeded cost limit: ${agent.session_costs['total_estimated_cost']:.2f}")
                await session.say("We've reached the session limit. Feel free to call back to continue!")
                await asyncio.sleep(2)
                await session.aclose()
                break

    # Start the limit checker
    limit_task = asyncio.create_task(check_limits_periodically())

    # ADD THIS: Handle silence detection in user transcription
    @session.on("user_input_transcribed")
    def on_user_transcribed(event):
        """Reset more aggressive timeouts on any user input."""
        # This ensures we reset timeouts when user speaks
        if hasattr(silence_manager, 'silence_start_time'):
            silence_manager.silence_start_time = None

    # ADD THIS: Enhanced close handler
    @session.on("close")
    def on_session_close(event):
        """Clean up on session close."""
        silence_manager.cleanup()
        limit_task.cancel()

        # Log why session ended
        if hasattr(agent, 'session_data'):
            disconnect_reason = agent.session_data.get("disconnect_reason", "user_initiated")
            logger.info(f"Session closed - Reason: {disconnect_reason}")
            logger.info(f"Session duration: {agent.session_data.get('duration_seconds', 0):.1f}s")
            logger.info(f"Total cost: ${agent.session_costs['total_estimated_cost']:.4f}")

    # ... rest of existing code ...
```

## Alternative: Simpler Built-in Approach

LiveKit also provides a simpler approach using just the `user_away_timeout`:

```python
# Simple approach - just use built-in timeout
session = AgentSession(
    # ... other config ...
    user_away_timeout=30,  # User marked "away" after 30s
)

# Handle the away state
@session.on("user_state_changed")
async def on_user_state_changed(event):
    if event.new_state == "away":
        # User has been silent for 30 seconds
        await session.say("Hello? I'm going to disconnect due to inactivity.")
        await asyncio.sleep(3)
        await session.aclose()
```

## Configuration Options

### 1. **Silence Timeout Settings**
```python
SilenceTimeoutManager(
    silence_timeout_seconds=30,     # Total silence before disconnect
    warning_before_disconnect=10,    # Warn N seconds before disconnect
)
```

### 2. **Session Limits**
```python
# In check_limits_periodically():
MAX_SESSION_DURATION = 1800  # 30 minutes
MAX_SESSION_COST = 5.0       # $5 per session
CHECK_INTERVAL = 30           # Check every 30 seconds
```

### 3. **User Away Detection**
```python
session = AgentSession(
    user_away_timeout=15,  # Seconds before marking user "away"
)
```

## Cost-Saving Benefits

With these controls in place:
- **30-second silence timeout**: Prevents "dead air" charges
- **30-minute session limit**: Caps maximum session duration
- **$5 cost limit**: Hard stop on expensive runaway sessions
- **Warning before disconnect**: User-friendly experience

### Estimated Savings
- Without limits: Accidental 2-hour call = ~$50
- With limits: Maximum possible charge = $5
- **Savings: 90% reduction in worst-case scenarios**

## Advanced Features

### 1. **Context-Aware Timeouts**
Use the `AdaptiveSilenceTimeout` class for smarter timeouts:
- 2x timeout when user says "let me think"
- 0.5x timeout during small talk
- Normal timeout for regular conversation

### 2. **Rate Limiting API Calls**
Use the `RateLimiter` class to limit:
- Knowledge base searches: Max 10 per minute
- Tool calls: Max 20 per minute
- Prevents abuse and reduces costs

### 3. **Telephony-Specific Settings**
For phone calls, use tighter limits:
```python
# Telephony optimizations
if ctx.room.metadata.get("source") == "telephony":
    silence_timeout = 20      # Shorter for phone calls
    max_duration = 900        # 15 min max for phone
    warning_time = 5          # Quick warning
```

## Testing

Test the silence detection locally:
```bash
# Start agent in console mode
uv run python src/agent.py console

# Test scenarios:
1. Start conversation, then go silent for 30s
2. Say "let me think" then go silent (should get longer timeout)
3. Let session run for 30 minutes (should auto-disconnect)
```

## Deployment

After adding silence detection:
```bash
# Deploy to LiveKit Cloud
lk agent deploy

# Monitor logs for silence disconnections
lk agent logs | grep -i "silence\|timeout\|disconnect"
```

## Monitoring

Track disconnection reasons in your analytics:
```python
# In export_session_data():
session_payload["disconnect_reason"] = agent.session_data.get("disconnect_reason")
session_payload["silence_events"] = agent.session_data.get("silence_count", 0)
```

This helps identify:
- How many sessions end due to silence
- Average session duration before timeout
- Cost savings from automatic disconnection