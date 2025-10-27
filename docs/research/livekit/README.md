# LiveKit Technical Research

Comprehensive technical research on LiveKit's Agents Framework for building production-ready voice AI agents. This directory contains deep-dive documentation covering all aspects of LiveKit development for the PandaDoc Voice Agent project.

## Overview

These documents provide complete technical references for LiveKit's Agents Framework, including detailed API documentation, code examples, architectural patterns, and best practices. Each guide is production-focused and informed by real-world implementation considerations.

---

## Documents

### [function-tools.md](./function-tools.md)
**AI Function Tools - Comprehensive Implementation Guide** (34K)

Complete guide to implementing AI function calling with LiveKit's Agents Framework. This is your primary reference for building the business logic integration layer.

**Contents:**
- Function tool architecture and patterns
- Tool definition with type hints and validation
- Argument parsing (primitive, enum, array, nested objects)
- Context management and state handling
- Error handling and recovery strategies
- Real-world implementation examples
- PandaDoc-specific function mappings

**Key Topics:**
- `@llm.ai_callable()` decorator usage
- `FunctionContext` lifecycle management
- Async function implementation
- Tool registration and discovery
- Integration with conversation flow

**Use this for:** Implementing all PandaDoc business operations (document creation, field verification, signature tracking, etc.)

---

### [testing-framework.md](./testing-framework.md)
**Testing Framework - Complete Testing Guide** (30K)

Comprehensive testing documentation covering unit, integration, and end-to-end testing patterns for LiveKit agents.

**Contents:**
- Testing architecture overview
- Unit testing with pytest and pytest-asyncio
- Integration testing patterns
- End-to-end testing with JobRunner
- Mock strategies and fixtures
- Test data management
- CI/CD integration
- Coverage and quality metrics

**Key Topics:**
- `JobRunner` for E2E testing
- `mock.AsyncMock` for async code
- Event-driven testing patterns
- Audio simulation and validation
- Conversation flow testing

**Use this for:** Building comprehensive test suites across all testing levels, ensuring production readiness.

---

### [testing-research.md](./testing-research.md)
**Testing Research - Findings and Analysis** (30K)

Research findings and analysis of testing approaches, including evaluation of different testing strategies and tools for LiveKit agents.

**Contents:**
- Testing methodology comparison
- Tool evaluation (pytest, AsyncMock, JobRunner)
- Best practices synthesis
- Common pitfalls and solutions
- Performance testing considerations
- Real-world testing scenarios

**Key Topics:**
- Testing strategy selection
- Mock vs real integration trade-offs
- Async testing patterns
- Event validation approaches

**Use this for:** Understanding testing philosophy and choosing appropriate testing strategies for different scenarios.

---

### [voice-pipeline.md](./voice-pipeline.md)
**Voice Pipeline Configuration - STT/TTS/VAD Guide** (27K)

Complete reference for configuring LiveKit's voice pipeline, including speech recognition, text-to-speech, and voice activity detection.

**Contents:**
- Speech-to-Text (STT) providers and configuration
  - Deepgram integration
  - Google Cloud Speech
  - Assembly AI
  - Azure Speech
- Text-to-Speech (TTS) providers
  - ElevenLabs configuration
  - OpenAI TTS
  - Azure TTS
  - Cartesia
- Voice Activity Detection (VAD)
- Audio processing pipeline
- Latency optimization
- Multi-language support
- Error handling and fallbacks

**Key Topics:**
- `VoicePipelineAgent` configuration
- STT provider comparison and selection
- TTS voice customization
- VAD sensitivity tuning
- Interruption handling

**Use this for:** Configuring the voice pipeline to match PandaDoc's quality, latency, and language requirements.

---

## Usage Recommendations

### Getting Started Path

1. **Start with Quick References** ([../quick-references/](../quick-references/)) - Get oriented
2. **Deep Dive Selectively** - Reference these comprehensive docs as needed
3. **Follow Implementation Plan** - Use alongside [../../implementation/IMPLEMENTATION_PLAN.md](../../implementation/IMPLEMENTATION_PLAN.md)

### By Development Phase

**Phase 1: Foundation (Weeks 1-2)**
- Start: `voice-pipeline.md` - Configure STT/TTS/VAD
- Reference: `function-tools.md` - Understand function tool architecture

**Phase 2: Core Features (Weeks 3-6)**
- Primary: `function-tools.md` - Implement all business operations
- Support: `testing-framework.md` - Build test coverage

**Phase 3: Integration (Weeks 7-8)**
- Primary: `testing-framework.md` - E2E testing
- Reference: All docs for debugging and optimization

**Phase 4: Production (Weeks 9-12)**
- Review: All docs for production readiness
- Focus: Error handling, monitoring, performance optimization

### By Role

**Backend Developers:**
- Primary: `function-tools.md`, `voice-pipeline.md`
- Secondary: `testing-framework.md`

**QA Engineers:**
- Primary: `testing-framework.md`, `testing-research.md`
- Reference: `function-tools.md` for understanding business logic

**DevOps/SRE:**
- Review: All docs for deployment considerations
- Focus: Error handling, monitoring, scaling sections

---

## Key Patterns & Concepts

### Function Tools Pattern
```python
@llm.ai_callable()
async def create_document(
    context: FunctionContext,
    document_name: str,
    recipient_email: str
):
    """Create a new PandaDoc document."""
    # Implementation
```

### Voice Pipeline Pattern
```python
agent = VoicePipelineAgent(
    vad=silero.VAD.load(),
    stt=deepgram.STT(),
    llm=openai.LLM(),
    tts=elevenlabs.TTS(),
)
```

### Testing Pattern
```python
@pytest.mark.asyncio
async def test_document_creation():
    async with JobRunner() as runner:
        # Test implementation
```

---

## Code Examples

All documents include production-ready code examples covering:
- Basic implementations
- Error handling
- Edge cases
- Performance optimization
- Integration patterns

Examples are based on:
- LiveKit Agents Framework v0.8+
- Python 3.9+
- Async/await patterns
- Type hints and validation

---

## Related Documentation

- **Quick References:** [../quick-references/](../quick-references/) - Condensed versions for rapid reference
- **Implementation Plan:** [../../implementation/IMPLEMENTATION_PLAN.md](../../implementation/IMPLEMENTATION_PLAN.md) - Epic-based development roadmap
- **Requirements Map:** [../../implementation/REQUIREMENTS_MAP.md](../../implementation/REQUIREMENTS_MAP.md) - PandaDoc to LiveKit mapping

---

## Document Maintenance

These documents are based on:
- LiveKit Agents Framework official documentation (January 2025)
- Python SDK v0.8+ API references
- Production deployment best practices
- PandaDoc Voice Agent requirements

For LiveKit updates and changes, consult:
- [LiveKit Official Docs](https://docs.livekit.io/)
- [LiveKit Python SDK GitHub](https://github.com/livekit/agents)
- [LiveKit Discord Community](https://livekit.io/discord)
