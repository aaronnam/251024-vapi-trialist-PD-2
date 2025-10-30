# TTS Troubleshooting Guide

This guide documents common TTS (Text-to-Speech) issues and their solutions for LiveKit Agents.

## ElevenLabs TTS Issues

### Issue: Audio Cuts Off After First Sentence

**Symptom:** The agent generates complete multi-sentence text, but TTS audio stops after the first sentence. Users only hear the first sentence spoken.

**Example:**
- **Expected:** "Hi! I'm your AI Pandadoc Trial Success Specialist. Before we begin, I need to let you know that our conversation will be transcribed..."
- **Actual audio:** "Hi! I'm your AI Pandadoc Trial Success Specialist." [stops]

#### Root Cause

The `auto_mode` parameter defaults to `True` in ElevenLabs TTS, which uses `SentenceTokenizer()` that processes text **one sentence at a time**. This is by design for low-latency applications, but causes audio to stop after the first sentence boundary when you need continuous multi-sentence speech.

**Technical details:**
- `auto_mode=True` (default) → Uses `tokenize.blingfire.SentenceTokenizer()`
- `auto_mode=False` → Uses `tokenize.basic.WordTokenizer(ignore_punctuation=False)`

#### Solution

Always explicitly set `auto_mode=False` for multi-sentence responses:

```python
from livekit.plugins import elevenlabs

tts=elevenlabs.TTS(
    voice_id="21m00Tcm4TlvDq8ikWAM",  # Your voice ID
    model="eleven_turbo_v2_5",
    streaming_latency=3,  # Recommended: 3-4 for stability
    auto_mode=False,  # CRITICAL: Prevents sentence-by-sentence cutoff
),
```

#### Additional Recommendations

1. **Update to latest plugin version:**
   ```toml
   # In pyproject.toml
   "livekit-plugins-elevenlabs~=1.2"
   ```

2. **Increase streaming latency for stability:**
   - `streaming_latency=3` or `streaming_latency=4`
   - Balances latency vs. reliability

3. **Test before deploying:**
   ```bash
   uv run python src/agent.py console
   ```
   Say a multi-sentence prompt to verify all sentences are spoken.

#### Debugging Commands

```bash
# Check for TTS-related errors
lk agent logs | grep -i "elevenlabs\|tts\|stream"

# Look for auto_mode warnings
lk agent logs | grep "auto_mode is enabled"

# Monitor TTS metrics
lk agent logs | grep "elevenlabs_characters"
```

#### When to Use `auto_mode=True`

Use `auto_mode=True` only when:
- You need extremely low latency (< 500ms)
- Your application sends **single-sentence** prompts
- You're building a low-latency conversational agent where each turn is one sentence

For most voice agents with natural multi-sentence responses, use `auto_mode=False`.

---

## Version History

### v1.2.15 (October 2024)
- **Status:** Recommended stable version
- Latest streaming improvements
- Better WebSocket connection handling

### v0.8.0 - v1.0.0
- Mid-range versions
- Some streaming issues reported

### v0.4.0
- **Status:** Broken TTS streaming (Issue #289)
- Do not use

---

## Testing Checklist

When configuring or changing TTS:

- [ ] Set `auto_mode=False` for multi-sentence responses
- [ ] Use `streaming_latency=3` or higher
- [ ] Update to `livekit-plugins-elevenlabs~=1.2`
- [ ] Test in console mode: `uv run python src/agent.py console`
- [ ] Say multi-sentence test prompt
- [ ] Verify all sentences are spoken
- [ ] Check logs for TTS errors
- [ ] Deploy only after local testing passes
- [ ] Restart agent after deployment: `lk agent restart`
- [ ] Test in Agent Playground with a new session

---

## Related Issues

### GitHub Issues
- **Issue #3667** (Oct 2024): Audio stops mid-playback
- **Issue #3293**: FallbackAdapter breaking native streaming
- **Issue #289**: TTS streaming broken in v0.4.0

### Commit References
- **Commit `6e26d8c`** (Oct 2024): Fix ElevenLabs TTS sentence cutoff issue

---

## Alternative TTS Providers

If ElevenLabs issues persist, consider these alternatives:

### Cartesia TTS (Sonic 2)
```python
from livekit.plugins import cartesia

tts=cartesia.TTS(
    voice="95856005-0332-41b0-935f-352e296aa0df",
    model="sonic-2-english",
)
```

**Pros:**
- Native streaming support
- No sentence cutoff issues
- Lower latency

**Cons:**
- Different voice quality than ElevenLabs
- May require voice ID mapping

### OpenAI TTS
```python
from livekit.plugins import openai

tts=openai.TTS(
    voice="nova",
    model="tts-1",
)
```

**Pros:**
- Reliable streaming
- Good voice quality
- Simple configuration

**Cons:**
- Higher latency than ElevenLabs
- Limited voice options

---

## Quick Reference

### Working Configuration (ElevenLabs)
```python
tts=elevenlabs.TTS(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    model="eleven_turbo_v2_5",
    streaming_latency=3,
    auto_mode=False,  # Critical for multi-sentence
)
```

### Test Command
```bash
uv run python src/agent.py console
```

### Debug Command
```bash
lk agent logs | grep -i "elevenlabs\|tts"
```

### Version Check
```bash
uv pip list | grep elevenlabs
```

---

## Contact & Support

For additional help:
- LiveKit Documentation: https://docs.livekit.io/agents/models/tts/
- LiveKit Discord: https://livekit.io/discord
- GitHub Issues: https://github.com/livekit/agents/issues

---

**Last Updated:** October 2024
**Applies To:** livekit-agents v1.2.x, livekit-plugins-elevenlabs v1.2.x
