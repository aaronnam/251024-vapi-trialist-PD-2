# Quick Reference Guides

Condensed, developer-friendly reference guides for LiveKit's Agents Framework. These are streamlined versions of the comprehensive research documentation, optimized for rapid lookup during active development.

## Overview

Quick references provide essential information in a scannable format:
- Key APIs and patterns
- Code snippets ready to adapt
- Common configurations
- Essential best practices

**Use these when:** You need fast answers while coding, not when learning concepts for the first time.

---

## Guides

### [function-tools-summary.md](./function-tools-summary.md)
**Function Tools Quick Reference**

Condensed guide to AI function calling with LiveKit. Essential patterns and APIs for implementing business logic integration.

**Quick Access To:**
- `@llm.ai_callable()` decorator syntax
- Function signatures and type hints
- Argument parsing examples (primitives, enums, arrays, objects)
- Context management patterns
- Error handling snippets
- Common integration patterns

**Example Usage:**
```python
@llm.ai_callable()
async def create_document(
    context: FunctionContext,
    name: str,
    email: str
) -> str:
    """Create document and return ID."""
    # Your implementation
```

**Use this for:** Quick lookup of function tool patterns while implementing PandaDoc business operations.

---

### [testing-quick-ref.md](./testing-quick-ref.md)
**Testing Patterns Quick Reference**

Fast reference for testing LiveKit agents. Essential patterns for unit, integration, and E2E testing.

**Quick Access To:**
- Test fixture setup
- `pytest-asyncio` patterns
- `JobRunner` for E2E tests
- Mock strategies
- Common assertions
- Test organization

**Example Usage:**
```python
@pytest.mark.asyncio
async def test_function_tool():
    async with JobRunner() as runner:
        # Test logic
```

**Use this for:** Writing tests quickly without digging through comprehensive testing documentation.

---

### [voice-pipeline-quick-ref.md](./voice-pipeline-quick-ref.md)
**Voice Pipeline Quick Reference**

Fast reference for STT/TTS/VAD configuration. Essential settings and provider configurations.

**Quick Access To:**
- `VoicePipelineAgent` setup
- STT provider configurations (Deepgram, Google, Azure)
- TTS provider settings (ElevenLabs, OpenAI, Azure)
- VAD configuration
- Common pipeline patterns
- Latency optimization tips

**Example Usage:**
```python
agent = VoicePipelineAgent(
    vad=silero.VAD.load(),
    stt=deepgram.STT(model="nova-2"),
    llm=openai.LLM(model="gpt-4"),
    tts=elevenlabs.TTS(voice="professional"),
)
```

**Use this for:** Quickly configuring or adjusting voice pipeline settings without reading full documentation.

---

## When to Use Quick References vs. Comprehensive Docs

### Use Quick References When:
- Actively writing code
- Need API syntax reminder
- Looking for a specific pattern
- Want copy-paste examples
- Time-sensitive development

### Use Comprehensive Docs When:
- Learning concepts for first time
- Debugging complex issues
- Need deep understanding
- Designing architecture
- Evaluating alternatives

**Path:** [../livekit/](../livekit/) for comprehensive documentation

---

## Reference Matrix

| Need | Quick Ref | Comprehensive Doc |
|------|-----------|-------------------|
| Function decorator syntax | function-tools-summary.md | livekit/function-tools.md |
| Pytest fixture setup | testing-quick-ref.md | livekit/testing-framework.md |
| STT provider config | voice-pipeline-quick-ref.md | livekit/voice-pipeline.md |
| Deep understanding | Use comprehensive docs | livekit/*.md |
| Edge case handling | Use comprehensive docs | livekit/*.md |

---

## How to Use These Guides

### During Development
1. **Keep open in editor** - Reference while coding
2. **Search by keyword** - Cmd/Ctrl+F for specific APIs
3. **Copy-paste patterns** - Adapt examples to your needs
4. **Validate quickly** - Check syntax and patterns

### For Code Review
1. **Pattern validation** - Ensure code follows documented patterns
2. **Quick checks** - Verify configuration values
3. **Best practice review** - Confirm adherence to guidelines

### For Onboarding
1. **Start here** - Get familiar with APIs
2. **Then deep dive** - Use comprehensive docs for learning
3. **Return frequently** - Use as daily reference

---

## Document Format

Each quick reference follows this structure:
- **Overview** - What the guide covers
- **Key Patterns** - Most common use cases
- **Code Examples** - Copy-paste ready snippets
- **Configuration** - Essential settings
- **Best Practices** - Quick tips
- **Related** - Links to comprehensive docs

---

## Relationship to Other Documentation

```
Quick References (You are here)
      |
      | Condensed from
      v
Comprehensive Research (../livekit/)
      |
      | Informs
      v
Implementation Plan (../../implementation/)
      |
      | Drives
      v
Production Code
```

---

## Quick Navigation

**For Implementation:**
- [Function Tools Summary](./function-tools-summary.md) - Business logic
- [Testing Quick Ref](./testing-quick-ref.md) - Test patterns
- [Voice Pipeline Quick Ref](./voice-pipeline-quick-ref.md) - STT/TTS/VAD

**For Deep Dives:**
- [LiveKit Research](../livekit/) - Comprehensive technical docs
- [Implementation Plan](../../implementation/IMPLEMENTATION_PLAN.md) - Development roadmap
- [Requirements Map](../../implementation/REQUIREMENTS_MAP.md) - PandaDoc to LiveKit mapping

---

## Maintenance

Quick references are maintained alongside comprehensive documentation. When LiveKit APIs change:
1. Update comprehensive docs first
2. Sync quick references with changes
3. Validate all code examples
4. Update version references

Based on LiveKit Agents Framework v0.8+ and Python 3.9+.
