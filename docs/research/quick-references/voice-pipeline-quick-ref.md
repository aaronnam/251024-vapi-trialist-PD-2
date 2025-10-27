# LiveKit Agents Voice Pipeline - Quick Reference Guide

## Configuration Quickstart

### Minimum Setup
```python
from livekit.agents import AgentSession

session = AgentSession(
    stt="deepgram/nova-3",
    tts="elevenlabs/eleven_turbo_v2_5",
)
```

### Production Setup
```python
from livekit.agents import AgentSession, RoomInputOptions, RoomOutputOptions
from livekit.agents.inference import STT, TTS
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Create session with all optimizations
session = AgentSession(
    stt=STT(model="deepgram/nova-3", language="en", sample_rate=16000),
    tts=TTS(model="elevenlabs/eleven_turbo_v2_5", voice="...", sample_rate=24000),
    turn_detection=MultilingualModel(),
    vad=silero.VAD.load(),
    allow_interruptions=True,
    min_endpointing_delay=0.5,
    max_endpointing_delay=3.0,
    preemptive_generation=True,
    false_interruption_timeout=2.0,
    resume_false_interruption=True,
    tts_text_transforms=["filter_markdown", "filter_emoji"],
)

# Connect to room with noise cancellation
await session.start(
    agent=my_agent,
    room=ctx.room,
    room_input_options=RoomInputOptions(
        audio_sample_rate=24000,
        noise_cancellation=noise_cancellation.BVC(),
    ),
    room_output_options=RoomOutputOptions(
        audio_sample_rate=24000,
        transcription_enabled=True,
    ),
)
```

## Provider Options

### Deepgram STT Options
```python
extra_kwargs = {
    "filler_words": True,           # Include filler words
    "interim_results": True,         # Real-time interim results
    "endpointing": 25,               # Endpointing delay (ms)
    "punctuate": True,               # Add punctuation
    "smart_format": True,            # Smart formatting
    "profanity_filter": False,       # Filter profanity
    "numerals": True,                # Format as numerals
    "keywords": [("hello", 1.5)],   # Keyword boosting
    "keyterms": ["livekit"],         # Key terms
    "mip_opt_out": False,            # MIP opt out
}

stt = STT(model="deepgram/nova-3", extra_kwargs=extra_kwargs)
```

### ElevenLabs TTS Options
```python
extra_kwargs = {
    "inactivity_timeout": 60,                    # Timeout (seconds)
    "apply_text_normalization": "auto",          # "auto", "off", "on"
}

tts = TTS(
    model="elevenlabs/eleven_turbo_v2_5",
    voice="pNInz6obpgDQGcFmaJgB",
    extra_kwargs=extra_kwargs,
)
```

## Parameter Tuning Guide

### For Fast Response (Minimal Latency)
```python
session = AgentSession(
    stt="deepgram/nova-3",
    tts="cartesia/sonic-turbo",  # Faster than ElevenLabs
    min_endpointing_delay=0.2,
    max_endpointing_delay=1.5,
    preemptive_generation=True,
    min_interruption_duration=0.3,
)
```

### For Accurate Results (Needs Time)
```python
session = AgentSession(
    stt="deepgram/nova-3",
    tts="elevenlabs/eleven_turbo_v2_5",
    min_endpointing_delay=0.8,
    max_endpointing_delay=4.0,
    preemptive_generation=False,
    min_interruption_duration=1.0,
)
```

### For Natural Conversation
```python
session = AgentSession(
    # ... basic config ...
    allow_interruptions=True,
    discard_audio_if_uninterruptible=True,
    min_interruption_duration=0.5,
    false_interruption_timeout=2.0,
    resume_false_interruption=True,
)
```

## Testing & Monitoring

### Collect Metrics
```python
from livekit.agents import metrics, MetricsCollectedEvent

usage_collector = metrics.UsageCollector()

@session.on("metrics_collected")
def on_metrics(ev: MetricsCollectedEvent):
    metrics.log_metrics(ev.metrics)
    usage_collector.collect(ev.metrics)

# Get summary
summary = usage_collector.get_summary()
```

### Listen to Events
```python
@session.on("user_state_changed")
def on_user_state(ev):
    print(f"User: {ev.new_state}")  # "listening", "speaking", "away"

@session.on("agent_state_changed")
def on_agent_state(ev):
    print(f"Agent: {ev.new_state}")  # "initializing", "listening", "thinking", "speaking"

@session.on("user_input_transcribed")
def on_transcribed(ev):
    print(f"Transcribed: {ev.text}")
```

## Deployment Checklist

- [ ] Pre-warm VAD in `prewarm()` function
- [ ] Configure noise cancellation (BVC for real-world)
- [ ] Set up metrics collection
- [ ] Configure connection retry logic (max_retry=2)
- [ ] Test with various audio qualities
- [ ] Tune endpointing delays for your use case
- [ ] Enable transcription for better UX
- [ ] Set user_away_timeout appropriately (15s default)
- [ ] Test false interruption recovery
- [ ] Monitor metrics in production

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Slow response | Lower min_endpointing_delay, enable preemptive_generation |
| Agent cuts off | Raise max_endpointing_delay, disable preemptive_generation |
| Too many false interruptions | Raise min_interruption_duration, adjust false_interruption_timeout |
| Poor audio quality | Raise audio_sample_rate to 24000, enable noise cancellation |
| High latency | Use TTS "cartesia/sonic-turbo", lower sample rate to 16000 |
| Frequent reconnections | Check connection options, increase max_retry |

## STT Model Selection by Use Case

| Use Case | Model | Note |
|----------|-------|------|
| General conversation | deepgram/nova-3 | Best all-around |
| Phone calls | deepgram/nova-2-phonecall | Optimized for phone audio |
| Medical | deepgram/nova-3-medical | Medical terminology |
| Real-time chat | deepgram/nova-2 | Faster than nova-3 |
| Budget-conscious | cartesia/ink-whisper | Good quality, lower cost |

## TTS Model Selection by Use Case

| Use Case | Model | Speed | Quality |
|----------|-------|-------|---------|
| Max latency | cartesia/sonic-turbo | Very fast | Good |
| Balanced | elevenlabs/eleven_turbo_v2_5 | Fast | Excellent |
| Premium quality | elevenlabs/eleven_flash_v2_5 | Fast | Excellent |
| Multilingual | elevenlabs/eleven_multilingual_v2 | Medium | Good |

## Resource Files

Full comprehensive guide: `/tmp/livekit_voice_pipeline_research.md`
Summary: `/tmp/research_summary.txt`

