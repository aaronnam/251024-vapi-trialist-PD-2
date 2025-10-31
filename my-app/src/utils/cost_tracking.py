"""
Cost calculation utilities for LiveKit Agent.

This module provides pricing information for various AI providers.
Costs are now tracked by enriching LiveKit's OpenTelemetry spans directly
in the metrics handler, rather than creating separate spans.

For cost tracking implementation, see agent.py:_on_metrics_collected()
"""

# Provider pricing (as of 2025-01, update periodically)
PROVIDER_PRICING = {
    # OpenAI pricing
    "openai_gpt4_mini_input": 0.000150 / 1000,  # $0.150 per 1M input tokens
    "openai_gpt4_mini_output": 0.000600 / 1000,  # $0.600 per 1M output tokens

    # Deepgram STT pricing (Nova 2)
    "deepgram_nova2": 0.0043 / 60,  # $0.0043 per minute → $/second for calculation

    # AssemblyAI STT pricing (Universal)
    "assemblyai_universal": 0.01 / 60,  # $0.01 per minute (estimated)

    # Cartesia TTS pricing (Sonic)
    "cartesia_sonic": 0.06 / 1000000,  # $60 per 1M characters

    # ElevenLabs TTS pricing (Turbo)
    "elevenlabs_turbo": 0.18 / 1000,  # $0.18 per 1K characters
}


def calculate_llm_cost(prompt_tokens: int, completion_tokens: int, model: str = "gpt-4.1-mini") -> dict:
    """
    Calculate LLM cost breakdown.

    Args:
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        model: Model name (currently only supports gpt-4.1-mini)

    Returns:
        Dictionary with input_cost, output_cost, and total_cost
    """
    input_cost = prompt_tokens * PROVIDER_PRICING["openai_gpt4_mini_input"]
    output_cost = completion_tokens * PROVIDER_PRICING["openai_gpt4_mini_output"]

    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
        "tokens": prompt_tokens + completion_tokens
    }


def calculate_stt_cost(audio_duration_seconds: float, provider: str = "deepgram") -> dict:
    """
    Calculate STT cost.

    Args:
        audio_duration_seconds: Duration of audio processed
        provider: STT provider (deepgram, assemblyai)

    Returns:
        Dictionary with cost and duration info
    """
    if provider == "deepgram":
        price_per_minute = PROVIDER_PRICING["deepgram_nova2"] * 60  # Convert back to per-minute
    elif provider == "assemblyai":
        price_per_minute = PROVIDER_PRICING["assemblyai_universal"] * 60
    else:
        price_per_minute = PROVIDER_PRICING["deepgram_nova2"] * 60

    minutes = audio_duration_seconds / 60.0
    cost = minutes * price_per_minute

    return {
        "cost": cost,
        "seconds": audio_duration_seconds,
        "minutes": minutes
    }


def calculate_tts_cost(character_count: int, provider: str = "cartesia") -> dict:
    """
    Calculate TTS cost.

    Args:
        character_count: Number of characters synthesized
        provider: TTS provider (cartesia, elevenlabs)

    Returns:
        Dictionary with cost and character count
    """
    if provider == "cartesia":
        price_per_char = PROVIDER_PRICING["cartesia_sonic"]
    elif provider == "elevenlabs":
        price_per_char = PROVIDER_PRICING["elevenlabs_turbo"] / 1000  # Convert from per 1K to per char
    else:
        price_per_char = PROVIDER_PRICING["cartesia_sonic"]

    cost = character_count * price_per_char

    return {
        "cost": cost,
        "characters": character_count
    }
