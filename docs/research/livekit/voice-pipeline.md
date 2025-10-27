# LiveKit Agents Voice Pipeline Configuration Research

## Overview
LiveKit Agents provides a comprehensive voice pipeline system with configurable STT (Speech-to-Text), TTS (Text-to-Speech), VAD (Voice Activity Detection), and turn detection components. This document covers production-ready configurations for optimal voice quality and low latency.

---

## 1. STT (Speech-to-Text) Provider Configuration

### Supported Providers
LiveKit Agents supports multiple STT providers through the inference system:

1. **Deepgram** - Primary streaming STT provider
   - Models: `deepgram/nova-3`, `deepgram/nova-3-general`, `deepgram/nova-3-medical`
   - Models: `deepgram/nova-2`, `deepgram/nova-2-general`, `deepgram/nova-2-medical`, `deepgram/nova-2-conversationalai`, `deepgram/nova-2-phonecall`
   - Default: `deepgram`

2. **Cartesia** - Alternative streaming STT
   - Models: `cartesia/ink-whisper`
   - Default: `cartesia`

3. **AssemblyAI** - Streaming STT with good interim results
   - Models: `assemblyai/universal-streaming`
   - Default: `assemblyai`

### Deepgram Configuration Example

```python
from livekit.agents.inference import STT

# Basic configuration
stt = STT(
    model="deepgram/nova-3",
    language="en"
)

# Advanced configuration with options
from livekit.agents.inference.stt import DeepgramOptions

deepgram_options: DeepgramOptions = {
    "filler_words": True,              # Include filler words in transcription
    "interim_results": True,            # Enable interim results for real-time feedback
    "endpointing": 25,                  # Endpointing duration in ms
    "punctuate": True,                  # Add punctuation
    "smart_format": True,               # Enable smart formatting
    "profanity_filter": False,          # Filter profanity
    "numerals": True,                   # Format numbers as numerals
    "keywords": [                       # Keywords to boost
        ("hello", 1.5),
        ("livekit", 2.0),
    ],
    "keyterms": ["livekit", "agent"],  # Key terms to improve detection
    "mip_opt_out": False,               # Opt out of MIP (Model Improvement Program)
}

stt = STT(
    model="deepgram/nova-3",
    language="en",
    extra_kwargs=deepgram_options,
    encoding="pcm_s16le",               # PCM 16-bit little-endian
    sample_rate=16000                   # 16kHz sample rate
)
```

### STT Capabilities

```python
# STT capabilities structure
@dataclass
class STTCapabilities:
    streaming: bool          # Whether streaming is supported
    interim_results: bool    # Whether interim results are provided
    diarization: bool = False  # Whether speaker identification is supported
```

### STT Connection Options

```python
@dataclass
class SessionConnectOptions:
    stt_conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS
    # Controls retry logic, timeouts for STT provider
    
@dataclass
class APIConnectOptions:
    max_retry: int = 2                  # Maximum retries on failure
    retry_backoff: float = 1.0          # Backoff multiplier for retries
```

### STT Speech Events

The STT system provides multiple event types:

```python
class SpeechEventType(Enum):
    START_OF_SPEECH = "start_of_speech"          # Speech detected
    INTERIM_TRANSCRIPT = "interim_transcript"    # Partial result (real-time)
    PREFLIGHT_TRANSCRIPT = "preflight_transcript"# Stable but not final
    FINAL_TRANSCRIPT = "final_transcript"        # Final, confident result
    RECOGNITION_USAGE = "recognition_usage"     # Metrics event
    END_OF_SPEECH = "end_of_speech"             # Speech ended
```

### Production STT Configuration

```python
# Recommended for production
session = AgentSession(
    stt="deepgram/nova-3",  # Can also use inference.STT(...) for advanced config
    # Other session settings...
)

# For telephony/quality applications, consider:
session = AgentSession(
    stt="deepgram/nova-2-phonecall",  # Optimized for phone audio
    # Other session settings...
)

# For medical/formal applications:
session = AgentSession(
    stt="deepgram/nova-3-medical",  # Specialized vocabulary
    # Other session settings...
)
```

---

## 2. TTS (Text-to-Speech) Provider Configuration

### Supported Providers

1. **Cartesia** - Low-latency streaming TTS
   - Models: `cartesia/sonic`, `cartesia/sonic-2`, `cartesia/sonic-turbo`

2. **ElevenLabs** - Natural-sounding voices
   - Models: `elevenlabs/eleven_flash_v2`, `elevenlabs/eleven_flash_v2_5`, `elevenlabs/eleven_turbo_v2`, `elevenlabs/eleven_turbo_v2_5`, `elevenlabs/eleven_multilingual_v2`

3. **Rime** - Text-to-speech with accent control
   - Models: `rime/mist`, `rime/mistv2`, `rime/arcana`

4. **Inworld** - Interactive character voices
   - Models: `inworld/inworld-tts-1`

### ElevenLabs Configuration Example

```python
from livekit.agents.inference import TTS
from livekit.agents.inference.tts import ElevenlabsOptions

# Basic configuration
tts = TTS(
    model="elevenlabs/eleven_turbo_v2_5",
    voice="pNInz6obpgDQGcFmaJgB"  # Pre-defined voice ID
)

# Advanced configuration with options
elevenlabs_options: ElevenlabsOptions = {
    "inactivity_timeout": 60,  # Timeout in seconds for streaming
    "apply_text_normalization": "auto",  # "auto", "off", or "on"
}

tts = TTS(
    model="elevenlabs/eleven_flash_v2_5",  # Fastest model
    voice="pNInz6obpgDQGcFmaJgB",
    encoding="pcm_s16le",
    sample_rate=24000,  # 24kHz for high quality
    extra_kwargs=elevenlabs_options
)
```

### Available ElevenLabs Voices

The project uses voice IDs in the format `"pNInz6obpgDQGcFmaJgB"`. Popular voices include:
- Professional: Sophia, Michael, George
- Conversational: Rachel, Marta, Domi
- Creative: Daniel, Freya, Bella

### Cartesia Configuration Example (Low-Latency)

```python
from livekit.agents.inference.tts import CartesiaOptions

cartesia_options: CartesiaOptions = {
    "speed": "normal",  # "slow", "normal", "fast"
    "duration": None    # Max duration in seconds
}

tts = TTS(
    model="cartesia/sonic-turbo",  # Fastest streaming model
    voice="voice-id",  # Cartesia voice ID
    encoding="pcm_s16le",
    sample_rate=24000,
    extra_kwargs=cartesia_options
)
```

### TTS Capabilities

```python
@dataclass
class TTSCapabilities:
    streaming: bool          # Whether streaming is supported
    aligned_transcript: bool = False  # Whether word-level timestamps are provided
```

### TTS Streaming vs Non-Streaming

```python
# Streaming TTS (for low-latency)
stream = tts.stream(conn_options=conn_options)
async with stream:
    stream.push_text("Hello")
    stream.push_text(" world!")
    stream.end_input()
    
    async for audio_frame in stream:
        # Process audio incrementally
        pass

# Non-streaming TTS
chunked_stream = tts.synthesize("Hello world", conn_options=conn_options)
async for audio_frame in chunked_stream:
    # Wait for complete synthesis
    pass
```

### Production TTS Configuration

```python
# For maximum quality and naturalness
session = AgentSession(
    tts="elevenlabs/eleven_flash_v2_5",  # or use inference.TTS(...)
    # Other settings...
)

# For lowest latency
session = AgentSession(
    tts="cartesia/sonic-turbo",
    # Other settings...
)

# For multilingual support
session = AgentSession(
    tts="elevenlabs/eleven_multilingual_v2",
    # Other settings...
)
```

---

## 3. Voice Pipeline Settings and Parameters

### AgentSession Voice Options Configuration

```python
@dataclass
class VoiceOptions:
    allow_interruptions: bool
    discard_audio_if_uninterruptible: bool
    min_interruption_duration: float
    min_interruption_words: int
    min_endpointing_delay: float
    max_endpointing_delay: float
    max_tool_steps: int
    user_away_timeout: float | None
    false_interruption_timeout: float | None
    resume_false_interruption: bool
    min_consecutive_speech_delay: float
    use_tts_aligned_transcript: bool
    preemptive_generation: bool
    tts_text_transforms: Sequence[TextTransforms] | None
```

### Complete Voice Pipeline Configuration

```python
from livekit.agents import AgentSession
from livekit.agents.inference import STT, TTS
from livekit.plugins.silero import VAD
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Configure STT
stt = STT(
    model="deepgram/nova-3",
    language="en",
    sample_rate=16000,
    encoding="pcm_s16le"
)

# Configure TTS
tts = TTS(
    model="elevenlabs/eleven_turbo_v2_5",
    voice="pNInz6obpgDQGcFmaJgB",
    sample_rate=24000,
    encoding="pcm_s16le"
)

# Configure VAD (Voice Activity Detection)
vad = VAD.load()  # Silero VAD by default

# Configure turn detection
turn_detector = MultilingualModel()

# Create session with optimized parameters
session = AgentSession(
    stt=stt,
    tts=tts,
    vad=vad,
    turn_detection=turn_detector,
    
    # Interruption handling
    allow_interruptions=True,                    # Allow user to interrupt agent
    discard_audio_if_uninterruptible=True,      # Drop audio while agent speaks
    min_interruption_duration=0.5,               # Minimum 0.5s to register interruption
    min_interruption_words=0,                    # Don't require minimum words
    
    # Endpointing (turn boundary detection)
    min_endpointing_delay=0.5,                  # Wait 0.5s after speech end signal
    max_endpointing_delay=3.0,                  # Force turn end after 3.0s
    
    # Tool execution
    max_tool_steps=3,                           # Max consecutive tool calls per turn
    
    # User state tracking
    user_away_timeout=15.0,                     # Mark user away after 15s silence
    false_interruption_timeout=2.0,             # Handle false interruptions after 2s
    resume_false_interruption=True,             # Resume agent speech if false interruption detected
    
    # Speech sequencing
    min_consecutive_speech_delay=0.0,           # No minimum delay between speeches
    
    # Text processing
    use_tts_aligned_transcript=False,           # Don't use TTS-aligned transcripts by default
    tts_text_transforms=["filter_markdown", "filter_emoji"],  # Clean up text
    
    # Performance optimization
    preemptive_generation=True,                 # Start generation while waiting for turn end
)
```

### Endpointing and Turn Detection Parameters Explained

```python
# Turn boundary detection timing:
# 1. User stops speaking (VAD detects end_of_speech)
# 2. Wait min_endpointing_delay (default 0.5s)
# 3. If speech resumes -> continue user turn
# 4. If no speech after min_endpointing_delay -> turn complete
# 5. Force end of turn after max_endpointing_delay (default 3.0s)

# For fast, responsive agents:
session = AgentSession(
    min_endpointing_delay=0.2,      # Quick response
    max_endpointing_delay=2.0,      # Don't wait too long
    preemptive_generation=True,     # Start generating while listening
)

# For accurate, non-interrupting agents:
session = AgentSession(
    min_endpointing_delay=0.8,      # Wait longer for confidence
    max_endpointing_delay=4.0,      # Allow longer utterances
    preemptive_generation=False,    # Wait for definitive turn end
)
```

### RoomIO Input/Output Configuration

```python
from livekit.agents import RoomInputOptions, RoomOutputOptions, AgentSession
from livekit.plugins import noise_cancellation

# Room input configuration
room_input_options = RoomInputOptions(
    text_enabled=True,                          # Enable text input from participants
    audio_enabled=True,                         # Enable audio input
    video_enabled=False,                        # Disable video input (optional)
    audio_sample_rate=24000,                    # Input sample rate
    audio_num_channels=1,                       # Mono audio
    noise_cancellation=noise_cancellation.BVC(), # Background Voice Cancellation
    pre_connect_audio=True,                     # Handle pre-connection audio
    pre_connect_audio_timeout=3.0,              # 3s timeout for pre-connect audio
    close_on_disconnect=True,                   # Close session on participant disconnect
)

# Room output configuration
room_output_options = RoomOutputOptions(
    transcription_enabled=True,                 # Publish transcriptions
    audio_enabled=True,                         # Publish audio
    audio_sample_rate=24000,                    # Output sample rate
    audio_num_channels=1,                       # Mono audio
    sync_transcription=True,                    # Sync transcription with audio
    transcription_speed_factor=1.0,             # 1x speed sync
)

# Start session with room configuration
await session.start(
    agent=assistant,
    room=ctx.room,
    room_input_options=room_input_options,
    room_output_options=room_output_options,
)
```

---

## 4. VAD (Voice Activity Detection) Configuration

### Supported VAD Providers

1. **Silero VAD** (Default, recommended)
   - Local, fast, high accuracy
   - Update interval: ~0.1s (10Hz)

2. **Other VAD implementations** can be used via custom adapters

### Silero VAD Configuration

```python
from livekit.plugins.silero import VAD as SileroVAD

# Load and configure Silero VAD
vad = SileroVAD.load()  # Uses default settings

# Advanced configuration (if available)
# vad = SileroVAD(model="silero_vad", language="en")
```

### VAD Event Types

```python
class VADEventType(Enum):
    START_OF_SPEECH = "start_of_speech"    # Speech detected
    INFERENCE_DONE = "inference_done"      # Inference complete
    END_OF_SPEECH = "end_of_speech"        # Speech ended
```

### VAD Events Structure

```python
@dataclass
class VADEvent:
    type: VADEventType
    samples_index: int              # Audio sample index
    timestamp: float                # Event timestamp in seconds
    speech_duration: float          # Duration of speech segment
    silence_duration: float         # Duration of silence segment
    frames: list[rtc.AudioFrame]   # Associated audio frames
    probability: float = 0.0        # Speech probability (INFERENCE_DONE only)
    inference_duration: float = 0.0 # Inference time (INFERENCE_DONE only)
    speaking: bool = False          # Whether speech detected
```

### VAD Capabilities

```python
@dataclass
class VADCapabilities:
    update_interval: float  # How often VAD processes audio (typically 0.1s)
```

### Production VAD Configuration

```python
# Standard configuration for most applications
session = AgentSession(
    vad=SileroVAD.load(),
    # Combine with turn detection:
    turn_detection=MultilingualModel(),
    # Other settings...
)

# For sensitive/noisy environments
session = AgentSession(
    vad=SileroVAD.load(),
    min_endpointing_delay=0.8,   # More conservative
    max_endpointing_delay=4.0,   # Allow longer utterances
)
```

### Pre-warming VAD (for deployment)

```python
from livekit.agents import JobProcess

def prewarm(proc: JobProcess):
    # Pre-load VAD model during worker initialization
    proc.userdata["vad"] = SileroVAD.load()

# Use in entrypoint
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],  # Use pre-loaded VAD
        # Other settings...
    )
```

---

## 5. Turn Detection and Interruption Handling

### Turn Detection Modes

```python
TurnDetectionMode = Union[
    Literal["stt"],          # Use STT end-of-utterance signals
    Literal["vad"],          # Use VAD start/stop signals
    Literal["realtime_llm"], # Use realtime LLM server detection
    Literal["manual"],       # Manually control turns
    _TurnDetector            # Custom turn detector
]
```

### Turn Detection Priority (Auto-Selection)

When not specified, LiveKit chooses in this order:
1. `realtime_llm` (if realtime model available)
2. `vad` (if VAD available)
3. `stt` (if STT available)
4. `manual` (fallback)

### MultilingualModel Turn Detector Configuration

```python
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Recommended for most applications
turn_detector = MultilingualModel()

session = AgentSession(
    turn_detection=turn_detector,
    # Other settings...
)
```

### Interruption Handling Configuration

```python
# Enable interruptions (default)
session = AgentSession(
    allow_interruptions=True,                   # User can interrupt
    discard_audio_if_uninterruptible=True,     # Drop audio while speaking
    min_interruption_duration=0.5,              # Minimum 0.5s to register
    min_interruption_words=0,                   # No minimum word count
    false_interruption_timeout=2.0,             # Recover after 2s silence
    resume_false_interruption=True,             # Resume generation if false interrupt
)

# Disable interruptions
session = AgentSession(
    allow_interruptions=False,
    discard_audio_if_uninterruptible=True,
)

# For multi-turn conversations (strict turn-taking)
session = AgentSession(
    allow_interruptions=False,
    discard_audio_if_uninterruptible=False,    # Keep buffered audio
    min_consecutive_speech_delay=0.5,          # Minimum delay between turns
)
```

### False Interruption Recovery

```python
# The system handles false interruptions:
# 1. User audio detected while agent speaking
# 2. marked as interruption if > min_interruption_duration
# 3. Agent speech paused/interrupted
# 4. Wait false_interruption_timeout (default 2.0s)
# 5. If no valid user transcript -> false interruption
# 6. If resume_false_interruption=True -> resume agent speech
# 7. Otherwise -> wait for new user input

session = AgentSession(
    false_interruption_timeout=2.0,    # Wait 2s for user input
    resume_false_interruption=True,    # Resume if timeout occurs
)
```

### Handling User Input Events

```python
# Listen for user state changes
@session.on("user_state_changed")
def on_user_state_changed(event):
    print(f"User state: {event.new_state}")
    # Possible states: "listening", "speaking", "away"

# Listen for transcription events
@session.on("user_input_transcribed")
def on_user_transcribed(event):
    print(f"User said: {event.text}")

# Listen for agent state changes
@session.on("agent_state_changed")
def on_agent_state_changed(event):
    print(f"Agent state: {event.new_state}")
    # Possible states: "initializing", "listening", "thinking", "speaking"

# Manually interrupt agent
session.interrupt(force=False)

# Manually control turns
session.commit_user_turn(
    transcript_timeout=2.0,      # Wait 2s for final transcript
    stt_flush_duration=2.0       # Add 2s silence to flush STT buffer
)
```

---

## 6. Best Practices for Voice Quality and Latency

### Audio Quality Settings

```python
# For maximum quality (24kHz, 16-bit)
room_input_options = RoomInputOptions(
    audio_sample_rate=24000,      # Higher sample rate = better quality
    audio_num_channels=1,
)

room_output_options = RoomOutputOptions(
    audio_sample_rate=24000,
    audio_num_channels=1,
)

# Minimum for acceptable quality (16kHz, 16-bit)
room_input_options = RoomInputOptions(
    audio_sample_rate=16000,      # Lower latency, acceptable quality
    audio_num_channels=1,
)
```

### Latency Optimization

```python
# Configuration for minimum latency
session = AgentSession(
    stt="deepgram/nova-3",              # Fast streaming STT
    tts="cartesia/sonic-turbo",         # Fastest TTS model
    
    # Aggressive endpointing
    min_endpointing_delay=0.2,          # Respond quickly
    max_endpointing_delay=1.5,          # Don't wait long
    
    # Preemptive generation
    preemptive_generation=True,         # Start generating before turn end
    
    # Interruption settings
    allow_interruptions=True,
    min_interruption_duration=0.3,      # Detect interruptions quickly
    
    # Other optimizations
    min_consecutive_speech_delay=0.0,   # No delay between turns
    discard_audio_if_uninterruptible=True,  # Don't buffer unnecessary audio
)
```

### Quality vs Latency Trade-offs

```python
# QUALITY OPTIMIZED
session_quality = AgentSession(
    stt="deepgram/nova-3",                  # More accurate
    tts="elevenlabs/eleven_turbo_v2_5",    # Most natural
    
    min_endpointing_delay=0.8,              # Wait for confidence
    max_endpointing_delay=4.0,              # Allow complex utterances
    preemptive_generation=False,            # Wait for definitive turn end
    
    min_interruption_duration=1.0,          # Higher threshold
    false_interruption_timeout=3.0,         # More recovery time
)

# LATENCY OPTIMIZED
session_latency = AgentSession(
    stt="deepgram/nova-2",                  # Faster processing
    tts="cartesia/sonic-turbo",            # Fastest TTS
    
    min_endpointing_delay=0.2,              # Quick response
    max_endpointing_delay=1.5,              # Enforce time limit
    preemptive_generation=True,             # Parallel processing
    
    min_interruption_duration=0.3,          # Responsive
    false_interruption_timeout=1.0,         # Quick recovery
)

# BALANCED (DEFAULT)
session_balanced = AgentSession(
    stt="deepgram/nova-3",
    tts="elevenlabs/eleven_turbo_v2_5",
    
    min_endpointing_delay=0.5,              # Moderate
    max_endpointing_delay=3.0,              # Reasonable
    preemptive_generation=True,             # Good latency
    
    min_interruption_duration=0.5,          # Normal
    false_interruption_timeout=2.0,         # Standard
)
```

### Noise Handling and Audio Processing

```python
from livekit.plugins import noise_cancellation

# Background Voice Cancellation (recommended for production)
room_input_options = RoomInputOptions(
    noise_cancellation=noise_cancellation.BVC(),  # Best for background speech/noise
)

# Or use standard noise cancellation
room_input_options = RoomInputOptions(
    noise_cancellation=noise_cancellation.NoiseSuppressionOptions(),
)

# Or disable (for high-quality, controlled environments)
room_input_options = RoomInputOptions(
    noise_cancellation=None,
)
```

### Connection Resilience

```python
from livekit.agents.voice.agent_session import SessionConnectOptions

# Configure connection retry logic
conn_options = SessionConnectOptions(
    stt_conn_options=APIConnectOptions(
        max_retry=2,              # Retry failed STT requests 2 times
        retry_backoff=1.0,        # Backoff multiplier
    ),
    llm_conn_options=APIConnectOptions(
        max_retry=2,
        retry_backoff=1.0,
    ),
    tts_conn_options=APIConnectOptions(
        max_retry=2,
        retry_backoff=1.0,
    ),
    max_unrecoverable_errors=3,  # Close session after 3 consecutive errors
)

session = AgentSession(
    stt=stt,
    tts=tts,
    # ...
    conn_options=conn_options,
)
```

### Metrics and Monitoring

```python
from livekit.agents import metrics, MetricsCollectedEvent

# Collect and log metrics
usage_collector = metrics.UsageCollector()

@session.on("metrics_collected")
def on_metrics_collected(ev: MetricsCollectedEvent):
    # Log metrics for monitoring
    metrics.log_metrics(ev.metrics)
    usage_collector.collect(ev.metrics)

# Get usage summary
summary = usage_collector.get_summary()
logger.info(f"Session usage: {summary}")
```

---

## 7. Complete Production-Ready Example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    RoomOutputOptions,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.agents.inference import STT, TTS
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
load_dotenv(".env.local")

class ProductionAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a professional voice AI assistant.
            Respond naturally, concisely, and helpfully.""",
        )

def prewarm(proc: JobProcess):
    # Pre-load models during worker initialization
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # Configure STT with Deepgram
    stt = STT(
        model="deepgram/nova-3",
        language="en",
        sample_rate=16000,
        encoding="pcm_s16le",
    )
    
    # Configure TTS with ElevenLabs
    tts = TTS(
        model="elevenlabs/eleven_turbo_v2_5",
        voice="pNInz6obpgDQGcFmaJgB",
        sample_rate=24000,
        encoding="pcm_s16le",
    )
    
    # Configure voice pipeline
    session = AgentSession(
        stt=stt,
        tts=tts,
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        
        # Interruption and turn handling
        allow_interruptions=True,
        discard_audio_if_uninterruptible=True,
        min_interruption_duration=0.5,
        min_endpointing_delay=0.5,
        max_endpointing_delay=3.0,
        
        # Performance
        preemptive_generation=True,
        max_tool_steps=3,
        
        # User tracking
        user_away_timeout=15.0,
        false_interruption_timeout=2.0,
        resume_false_interruption=True,
        
        # Text processing
        tts_text_transforms=["filter_markdown", "filter_emoji"],
    )
    
    # Set up metrics collection
    usage_collector = metrics.UsageCollector()
    
    @session.on("metrics_collected")
    def on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)
    
    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")
    
    ctx.add_shutdown_callback(log_usage)
    
    # Start the session
    await session.start(
        agent=ProductionAssistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            audio_sample_rate=24000,
            audio_num_channels=1,
            noise_cancellation=noise_cancellation.BVC(),
            pre_connect_audio=True,
        ),
        room_output_options=RoomOutputOptions(
            audio_sample_rate=24000,
            audio_num_channels=1,
            transcription_enabled=True,
        ),
    )
    
    # Connect to the room
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
```

---

## 8. Summary: Key Configuration Parameters

| Parameter | Default | Recommended Range | Notes |
|-----------|---------|-------------------|-------|
| min_endpointing_delay | 0.5s | 0.2-1.0s | Lower = faster response, higher = more accurate |
| max_endpointing_delay | 3.0s | 1.5-4.0s | Maximum time to wait for turn end |
| min_interruption_duration | 0.5s | 0.3-1.0s | Minimum speech length to register interruption |
| false_interruption_timeout | 2.0s | 1.0-3.0s | Time to wait before recovering from false interruption |
| audio_sample_rate | 16000 | 16000-24000 | Higher = better quality, higher latency |
| STT encoding | pcm_s16le | pcm_s16le | Standard 16-bit PCM |
| user_away_timeout | 15.0s | 10-30s | Time to mark user as away |
| preemptive_generation | False | True/False | Enable parallel processing for lower latency |

