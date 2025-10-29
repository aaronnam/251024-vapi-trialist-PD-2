# Migrate from LiveKit Inference to Direct Provider Plugins

**Purpose**: Switch from LiveKit Inference (usage limits, $2.50/month free tier) to direct provider plugins (your own API keys, no LiveKit limits)

**When to use this guide**: When you hit LiveKit Cloud API usage limits or need full provider features (custom voices, fine-tuned models, etc.)

---

## Prerequisites

Ensure you have API keys for your providers:
- `OPENAI_API_KEY` - Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- `DEEPGRAM_API_KEY` - Get from [Deepgram Console](https://console.deepgram.com/)
- `ELEVENLABS_API_KEY` - Get from [ElevenLabs Settings](https://elevenlabs.io/app/settings/api-keys)

Add these to `my-app/.env.local` (keep LiveKit keys too - they're still needed for WebRTC infrastructure)

---

## Migration Steps

### 1. Install Missing Plugin Dependencies

```bash
cd my-app
uv add "livekit-agents[openai]~=1.2"
uv add "livekit-agents[deepgram]~=1.2"
```

**Note**: `livekit-plugins-elevenlabs` is already installed in your `pyproject.toml`

**What this does**: Adds provider-specific plugins to your project as optional dependencies on the base SDK

---

### 2. Update Imports in `agent.py`

**Find** (around line 28):
```python
from livekit.plugins import noise_cancellation, silero
```

**Replace with**:
```python
from livekit.plugins import noise_cancellation, silero, openai, deepgram, elevenlabs
```

**What this does**: Imports the plugin modules so you can instantiate their STT/LLM/TTS classes

---

### 3. Update AgentSession Configuration

**Find** (around lines 958-982 in the `entrypoint` function):
```python
session = AgentSession(
    stt="deepgram/nova-2:en",
    llm="openai/gpt-4.1-mini",
    tts="elevenlabs/eleven_turbo_v2_5:21m00Tcm4TlvDq8ikWAM",
    turn_detection=MultilingualModel(),
    vad=ctx.proc.userdata["vad"],
    preemptive_generation=True,
)
```

**Replace with**:
```python
session = AgentSession(
    # Direct provider plugins (bypass LiveKit Inference)
    stt=deepgram.STT(
        model="nova-2",
        language="en",
    ),
    llm=openai.LLM(
        model="gpt-4.1-mini",  # Keep the same model
        temperature=0.7,
    ),
    tts=elevenlabs.TTS(
        voice="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
        model="eleven_turbo_v2_5",
    ),
    turn_detection=MultilingualModel(),
    vad=ctx.proc.userdata["vad"],
    preemptive_generation=True,
)
```

**Key changes**:
- **STT**: String descriptor → `deepgram.STT()` instance
- **LLM**: String descriptor → `openai.LLM()` instance (same model name)
- **TTS**: String descriptor → `elevenlabs.TTS()` instance
  - **Voice**: Use `voice` parameter (not `voice_id`), not embedded in the string

---

### 4. Verify Environment Variables

Check that `my-app/.env.local` has all required keys:

```bash
# Should already be present:
OPENAI_API_KEY=sk-proj-...
DEEPGRAM_API_KEY=...
ELEVEN_API_KEY=sk_...  # ElevenLabs plugin uses ELEVEN_API_KEY

# Keep these (still needed for WebRTC):
LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
```

**Note**: The ElevenLabs plugin looks for `ELEVEN_API_KEY` (not `ELEVENLABS_API_KEY`). If you have `ELEVENLABS_API_KEY`, add:
```bash
ELEVEN_API_KEY=<same-value-as-ELEVENLABS_API_KEY>
```

**What this does**: Plugins read API keys from environment variables automatically

---

### 5. Test the Agent

**Console mode** (terminal-based testing):
```bash
cd my-app
uv run python src/agent.py console
```

**Dev mode** (for use with frontend/telephony):
```bash
cd my-app
uv run python src/agent.py dev
```

**What to verify**:
- Agent starts without errors
- Speech recognition works (STT via Deepgram)
- Agent responds (LLM via OpenAI)
- Voice output plays (TTS via ElevenLabs)

**Common issues**:
- **Missing API key**: Check `.env.local` has all three provider keys
- **Invalid model name**: Verify model names match provider documentation
- **Import error**: Ensure `uv add` commands completed successfully

---

## Verification Checklist

- [ ] Plugins installed: `uv pip list | grep livekit-plugins` shows `openai`, `deepgram`, `elevenlabs`
- [ ] Imports added: `from livekit.plugins import openai, deepgram, elevenlabs`
- [ ] AgentSession updated: Uses plugin instances (e.g., `openai.LLM()`) not strings
- [ ] Environment variables set: All three provider API keys in `.env.local`
- [ ] Agent runs: `uv run python src/agent.py console` starts successfully
- [ ] Voice pipeline works: Can speak to agent and get responses

---

## Cost Impact

**Before (LiveKit Inference)**:
- Free tier: $2.50/month in credits
- 5 concurrent STT/TTS connections
- Limited model selection

**After (Direct Providers)**:
- OpenAI: Pay-as-you-go (typically <$5/month for development)
- Deepgram: Pay-as-you-go (~$0.43/hour)
- ElevenLabs: Pay-as-you-go ($150/1M chars, or free tier)
- **No LiveKit usage limits** (only WebRTC limits: 100 participants on free plan)

**Expected monthly cost** (assuming 10k sessions × 5 min):
- STT: ~$385/month
- LLM: ~$1-2/month
- TTS: ~$30/month
- **Total: ~$416/month** (scales with usage)

---

## Rollback Plan

If you need to revert to LiveKit Inference:

1. **Revert `agent.py` imports**:
   ```python
   from livekit.plugins import noise_cancellation, silero
   ```

2. **Revert AgentSession**:
   ```python
   session = AgentSession(
       stt="deepgram/nova-2:en",
       llm="openai/gpt-4.1-mini",
       tts="elevenlabs/eleven_turbo_v2_5:21m00Tcm4TlvDq8ikWAM",
       # ... rest of config
   )
   ```

3. **Optional**: Remove plugins (they don't hurt if unused)
   ```bash
   uv remove livekit-agents[openai]
   uv remove livekit-agents[deepgram]
   ```

---

## Advanced Configuration

### Custom Voice with ElevenLabs

Use [voice cloning](https://elevenlabs.io/docs/voices/voice-cloning) for branded voice:

```python
tts=elevenlabs.TTS(
    voice_id="your-cloned-voice-id",  # From ElevenLabs Voice Lab
    model="eleven_multilingual_v2",   # Supports 29 languages
    voice_settings={
        "stability": 0.5,
        "similarity_boost": 0.8,
    },
)
```

### Optimized Models for Telephony

For phone calls, use telephony-optimized models:

```python
stt=deepgram.STT(
    model="nova-2-phonecall",  # Optimized for phone audio
    language="en",
)
```

### Fine-Tuned OpenAI Models

Use your custom fine-tuned models:

```python
llm=openai.LLM(
    model="ft:gpt-4o-mini-2024-07-18:your-org::123abc",  # Your fine-tuned model
    temperature=0.7,
)
```

---

## Reference Documentation

- **OpenAI Plugin**: https://docs.livekit.io/agents/models/llm/plugins/openai
- **Deepgram Plugin**: https://docs.livekit.io/agents/models/stt/plugins/deepgram
- **ElevenLabs Plugin**: https://docs.livekit.io/agents/models/tts/plugins/elevenlabs
- **Model Overview**: https://docs.livekit.io/agents/models
- **LiveKit MCP Server**: Use `claude mcp add --transport http livekit-docs https://docs.livekit.io/mcp` for instant docs access

---

## Troubleshooting

### Error: "No module named 'livekit.plugins.openai'"

**Cause**: Plugin not installed

**Fix**:
```bash
cd my-app
uv add "livekit-agents[openai]~=1.2"
```

### Error: "Invalid API key" or "Authentication failed"

**Cause**: Missing or incorrect API key in `.env.local`

**Fix**:
1. Check key format (e.g., OpenAI keys start with `sk-proj-` or `sk-`)
2. Verify key is valid at provider's dashboard
3. Ensure no extra quotes or spaces in `.env.local`

### Agent connects but doesn't respond

**Cause**: Plugin configuration issue (wrong model name, missing parameters)

**Fix**:
1. Check model names match provider documentation
2. Review logs: `uv run python src/agent.py console` shows detailed errors
3. Test each plugin individually by temporarily commenting out others

### Voice sounds robotic or low quality

**Cause**: TTS voice settings not optimized

**Fix**:
```python
tts=elevenlabs.TTS(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    model="eleven_turbo_v2_5",
    voice_settings={
        "stability": 0.5,       # 0-1, lower = more varied
        "similarity_boost": 0.8, # 0-1, higher = more like original
    },
)
```

---

## Next Steps

After successful migration:

1. **Monitor costs**: Track API usage at provider dashboards
2. **Optimize models**: Experiment with faster/cheaper models for development
3. **Add failover**: Implement fallback providers for production reliability
4. **Custom voices**: Clone voices for brand consistency (ElevenLabs Voice Lab)
5. **Fine-tune LLM**: Train custom OpenAI model on PandaDoc-specific knowledge

---

**Last updated**: 2025-10-29
**Applies to**: LiveKit Agents Python SDK v1.2+
