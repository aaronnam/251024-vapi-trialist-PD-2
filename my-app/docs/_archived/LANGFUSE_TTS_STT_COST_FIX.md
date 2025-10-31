# Fix: Making TTS/STT Costs Visible in Langfuse Model Usage

## Problem Summary
Only `gpt-4.1-mini` costs appear in Langfuse Model Usage dashboard ($0.294893 total) because:
- Langfuse only tracks costs for "generation" and "embedding" observation types
- Your TTS/STT tracking creates generic spans, not generation observations
- Langfuse doesn't have built-in model definitions for Deepgram, Cartesia, etc.

## Immediate Solution (No Code Changes)

### Step 1: Add Custom Model Definitions in Langfuse

1. Go to your Langfuse project settings
2. Navigate to **Model Definitions**
3. Add these custom models:

#### Deepgram Nova-2 (STT)
```
Model Name: deepgram-nova-2
Match Pattern: (?i)^(deepgram[-_]nova[-_]2)$
Unit: MINUTES
Input Price: 0.0043
Output Price: 0
Tokenizer: (leave empty)
```

#### Cartesia Sonic-3 (TTS)
```
Model Name: cartesia-sonic-3
Match Pattern: (?i)^(cartesia[-_]sonic[-_]3)$
Unit: CHARACTERS
Input Price: 0.00000006
Output Price: 0
Tokenizer: (leave empty)
```

#### AssemblyAI Universal (STT)
```
Model Name: assemblyai-universal
Match Pattern: (?i)^(assemblyai[-_]universal)$
Unit: MINUTES
Input Price: 0.01
Output Price: 0
Tokenizer: (leave empty)
```

### Step 2: Update Code to Create Generation Observations

The issue is that your `cost_tracking.py` creates generic spans. Langfuse needs "generation" observations for the Model Usage dashboard.

**Current code (not working for Model Usage):**
```python
# In cost_tracking.py line 157-167
with self.tracer.start_as_current_span("stt_usage") as span:
    span.set_attribute("langfuse.cost.total", total_cost)
    span.set_attribute("langfuse.model", f"{provider}_{model}")
```

**Fixed code (will work for Model Usage):**
```python
# Option A: Use Langfuse SDK directly
from langfuse import Langfuse

class CostTracker:
    def __init__(self):
        # ... existing code ...
        self.langfuse = Langfuse()  # Add this

    def track_stt_cost(self, audio_duration_seconds: float, provider: str = "deepgram",
                      model: str = "nova-2", speech_id: Optional[str] = None) -> float:
        # ... existing cost calculation ...

        # Create a generation observation for Model Usage tracking
        generation = self.langfuse.generation(
            name=f"stt_{provider}",
            model=f"{provider}-{model}",  # e.g., "deepgram-nova-2"
            input={"audio_seconds": audio_duration_seconds},
            output={"transcript": "placeholder"},  # Langfuse requires output
            usage={
                "input": minutes,  # Will be multiplied by model's input price
                "unit": "MINUTES"
            },
            metadata={
                "speech_id": speech_id or "no_speech_id",
                "provider": provider
            }
        )

        return total_cost

    def track_tts_cost(self, character_count: int, provider: str = "cartesia",
                      model: str = "sonic-3", speech_id: Optional[str] = None) -> float:
        # ... existing cost calculation ...

        # Create a generation observation for Model Usage tracking
        generation = self.langfuse.generation(
            name=f"tts_{provider}",
            model=f"{provider}-{model}",  # e.g., "cartesia-sonic-3"
            input={"text_length": character_count},
            output={"audio": "generated"},  # Langfuse requires output
            usage={
                "input": character_count,  # Will be multiplied by model's input price
                "unit": "CHARACTERS"
            },
            metadata={
                "speech_id": speech_id or "no_speech_id",
                "provider": provider
            }
        )

        return total_cost
```

## Alternative: Use LiveKit's Native Spans

LiveKit is already creating spans for TTS (`tts_request`) and potentially STT. You could:

1. Check if LiveKit's `tts_request` span has the right attributes
2. If yes, just add the model definitions in Langfuse UI
3. The costs might automatically appear

From your screenshots, LiveKit's `tts_request` already has:
- `lk.tts.label` = "livekit.plugins.cartesia.tts.TTS"
- `lk.tts_metrics` with 13 items (likely includes character count)

The problem is it doesn't have:
- `gen_ai.request.model` = "cartesia-sonic-3"
- `gen_ai.usage.input` = character_count

## Verification Steps

After implementing:

1. Make a test call to generate new traces
2. Check Langfuse Model Usage dashboard
3. You should see:
   - `gpt-4.1-mini` (already working)
   - `deepgram-nova-2` (new)
   - `cartesia-sonic-3` (new)

## Cost Calculation Verification

Current costs in your session:
- Total: $0.003951
- GPT-4.1-mini shown: $0.294893 (seems high - might be accumulated over time)

Expected breakdown per call:
- LLM: ~$0.0005-0.002 per turn (3000 tokens @ $0.15/1M input + $0.60/1M output)
- STT: ~$0.0002 per turn (3 seconds @ $0.0043/minute)
- TTS: ~$0.0001 per turn (100 chars @ $60/1M chars)

## Summary

**Root Cause**: Langfuse Model Usage only tracks "generation" type observations with recognized model names.

**Fix**:
1. Add custom model definitions in Langfuse UI (5 minutes)
2. Update `cost_tracking.py` to create generation observations instead of generic spans (30 minutes)
3. Or investigate if LiveKit's native spans can be enriched with the right attributes

**Result**: Full cost visibility across LLM, STT, and TTS in the Model Usage dashboard.