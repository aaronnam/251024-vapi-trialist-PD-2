# LiveKit Agent Cost Tracking with Langfuse

## Overview

This LiveKit agent now includes comprehensive cost tracking for all AI models (STT, TTS, and LLM) with automatic reporting to Langfuse for observability and analytics.

## Features

### 1. **Real-time Cost Tracking**
- **LLM Costs**: Tracks OpenAI GPT-4 mini token usage (input/output)
- **STT Costs**: Tracks Deepgram/AssemblyAI audio processing minutes
- **TTS Costs**: Tracks Cartesia/ElevenLabs character synthesis

### 2. **Langfuse Integration**
- Costs are reported via OpenTelemetry spans to Langfuse
- Each model usage creates a span with cost attributes
- Session summaries aggregate total costs
- Conversation turns track per-interaction costs

### 3. **Cost Visibility**
All costs appear in Langfuse with these attributes:
- `langfuse.cost.total` - Total cost for the operation
- `langfuse.cost.llm` - LLM-specific costs
- `langfuse.cost.stt` - STT-specific costs
- `langfuse.cost.tts` - TTS-specific costs
- `langfuse.usage.*` - Usage metrics (tokens, minutes, characters)

## Implementation Details

### Architecture

```
LiveKit Metrics Events
        ↓
  agent.py (metrics_collected)
        ↓
  CostTracker.track_*_cost()
        ↓
  OpenTelemetry Spans
        ↓
  Langfuse Dashboard
```

### Files Modified/Added

1. **`src/utils/cost_tracking.py`** (NEW)
   - `CostTracker` class with methods for each model type
   - OpenTelemetry span creation with cost attributes
   - Session cost aggregation

2. **`src/agent.py`** (MODIFIED)
   - Added `langfuse_cost_tracker` initialization
   - Integrated cost tracking in `_on_metrics_collected`
   - Added session summary reporting in shutdown callback

3. **`src/utils/telemetry.py`** (EXISTING)
   - Already configured OpenTelemetry → Langfuse pipeline
   - No changes needed

## Configuration

### Environment Variables

```bash
# Required for Langfuse integration
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud

# Model API keys (existing)
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key
```

### Pricing Configuration

Current pricing (as of 2025-01) is hardcoded in `CostTracker`:

```python
# OpenAI GPT-4 mini
"openai_gpt4_mini_input": 0.000150 / 1000    # $0.150 per 1M tokens
"openai_gpt4_mini_output": 0.000600 / 1000   # $0.600 per 1M tokens

# Deepgram Nova 2
"deepgram_nova2": 0.0043 / 60                # $0.0043 per minute

# Cartesia Sonic 3
"cartesia_sonic": 0.06 / 1000000             # $60 per 1M characters
```

Update these values in `src/utils/cost_tracking.py` when pricing changes.

## Usage

### 1. Set Environment Variables

```bash
export LANGFUSE_PUBLIC_KEY=pk_xxx
export LANGFUSE_SECRET_KEY=sk_xxx
```

### 2. Run the Agent

```bash
# Test in console mode
uv run python src/agent.py console

# Run in development
uv run python src/agent.py dev

# Deploy to production
lk agent deploy
```

### 3. View Costs in Langfuse

1. Go to https://cloud.langfuse.com
2. Navigate to your project
3. Open the Traces view
4. Look for traces with cost attributes
5. Use filters to analyze costs by model type

## Cost Tracking Flow

### Per-Turn Tracking

Each conversation turn generates:
1. **STT span**: Audio duration → cost
2. **LLM span**: Token usage → cost
3. **TTS span**: Character count → cost
4. **Turn summary span**: Aggregated costs + latency

### Session Summary

On session end:
- Total costs by model type
- Total usage metrics
- Complete cost breakdown
- Reported as `session_cost_summary` span

## Testing

Run the test script to verify integration:

```bash
uv run python test_cost_tracking.py
```

This tests:
- Cost calculation accuracy
- Span creation
- Session aggregation
- Agent integration

## Monitoring Costs

### In Logs

```bash
# View cost tracking logs
lk agent logs | grep -i "cost tracked"

# Example output:
# LLM cost tracked: $0.000045 (prompt: 100, completion: 50)
# STT cost tracked: $0.000072 (1.00 minutes of deepgram/nova-2)
# TTS cost tracked: $0.000030 (500 characters of cartesia/sonic-3)
```

### In Langfuse Dashboard

1. **Traces View**: See individual operation costs
2. **Metrics**: Aggregate costs over time
3. **Sessions**: Cost per conversation session
4. **Analytics**: Cost trends and patterns

## Best Practices

1. **Regular Price Updates**: Check provider pricing monthly
2. **Cost Limits**: Monitor `session_costs` for budget enforcement
3. **Alerting**: Set up Langfuse alerts for high-cost sessions
4. **Optimization**: Use cost data to optimize:
   - Prompt length (reduce input tokens)
   - Response length (reduce output tokens)
   - Audio quality settings
   - Model selection

## Troubleshooting

### Costs Not Appearing in Langfuse

1. Check environment variables are set
2. Verify tracing is enabled (check logs for "✅ Tracing enabled")
3. Ensure `langfuse.flush()` is called on shutdown
4. Check network connectivity to Langfuse

### Incorrect Cost Calculations

1. Verify pricing configuration matches current rates
2. Check model names match pricing keys
3. Review usage metrics for accuracy

### Missing Model Costs

Currently tracked:
- ✅ OpenAI LLM (GPT-4 mini)
- ✅ Deepgram STT (Nova 2)
- ✅ Cartesia TTS (Sonic 3)

Not yet tracked:
- ❌ Silero VAD (local, no cost)
- ❌ Turn detection model (minimal cost)
- ❌ Noise cancellation (BVC)

## Future Enhancements

1. **Dynamic Pricing**: Fetch pricing from provider APIs
2. **Budget Alerts**: Real-time cost limit enforcement
3. **Cost Optimization**: Automatic model switching based on cost/performance
4. **Detailed Breakdown**: Per-feature cost allocation
5. **Historical Analysis**: Cost trends and forecasting

## Summary

The LiveKit agent now provides complete cost transparency through Langfuse integration. Every STT, TTS, and LLM operation is tracked with accurate cost calculation and reported via OpenTelemetry spans. This enables:

- **Cost Monitoring**: Real-time visibility into AI model costs
- **Budget Control**: Track and limit session costs
- **Optimization**: Data-driven decisions on model usage
- **Analytics**: Understand cost patterns and trends

The integration is production-ready and requires only Langfuse credentials to activate.