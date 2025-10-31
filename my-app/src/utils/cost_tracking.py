"""
Cost tracking integration for LiveKit Agent with Langfuse.

This module provides comprehensive cost tracking for STT, TTS, and LLM models,
reporting costs to Langfuse for observability and analytics.

Based on research from Langfuse documentation:
- https://langfuse.com/docs/model-usage-and-cost
- https://langfuse.com/docs/integrations/frameworks/livekit
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from opentelemetry import trace

logger = logging.getLogger(__name__)


class CostTracker:
    """Track and report costs for various model providers to Langfuse."""

    def __init__(self):
        """Initialize cost tracker with provider pricing."""
        # Provider pricing (as of 2025-01, update periodically)
        self.provider_pricing = {
            # OpenAI pricing
            "openai_gpt4_mini_input": 0.000150 / 1000,  # $0.150 per 1M input tokens
            "openai_gpt4_mini_output": 0.000600 / 1000,  # $0.600 per 1M output tokens

            # Deepgram STT pricing (Nova 2)
            "deepgram_nova2": 0.0043 / 60,  # $0.0043 per minute

            # AssemblyAI STT pricing (Universal)
            "assemblyai_universal": 0.01 / 60,  # $0.01 per minute (estimated)

            # Cartesia TTS pricing (Sonic)
            "cartesia_sonic": 0.06 / 1000000,  # $60 per 1M characters (Sonic 3)

            # ElevenLabs TTS pricing (Turbo)
            "elevenlabs_turbo": 0.18 / 1000,  # $0.18 per 1K characters
        }

        # Session cost accumulator
        self.session_costs = {
            "llm": {"tokens": 0, "cost": 0.0},
            "stt": {"minutes": 0.0, "cost": 0.0},
            "tts": {"characters": 0, "cost": 0.0},
            "total": 0.0
        }

        # Get tracer for OpenTelemetry integration
        self.tracer = trace.get_tracer(__name__)

    def track_llm_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4.1-mini",
        speech_id: Optional[str] = None
    ) -> float:
        """
        Track LLM usage and costs, reporting to Langfuse.

        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            model: Model name for pricing lookup
            speech_id: Optional speech turn identifier

        Returns:
            Total cost for this LLM call
        """
        # Calculate costs
        input_cost = prompt_tokens * self.provider_pricing["openai_gpt4_mini_input"]
        output_cost = completion_tokens * self.provider_pricing["openai_gpt4_mini_output"]
        total_cost = input_cost + output_cost

        # Update session totals
        self.session_costs["llm"]["tokens"] += prompt_tokens + completion_tokens
        self.session_costs["llm"]["cost"] += total_cost
        self.session_costs["total"] += total_cost

        # Report to Langfuse via OpenTelemetry span
        try:
            with self.tracer.start_as_current_span("llm_usage") as span:
                # Set standard Langfuse cost attributes
                span.set_attribute("langfuse.cost.total", total_cost)
                span.set_attribute("langfuse.cost.input", input_cost)
                span.set_attribute("langfuse.cost.output", output_cost)

                # Set usage details
                span.set_attribute("langfuse.usage.prompt_tokens", prompt_tokens)
                span.set_attribute("langfuse.usage.completion_tokens", completion_tokens)
                span.set_attribute("langfuse.usage.total_tokens", prompt_tokens + completion_tokens)

                # Set model information
                span.set_attribute("langfuse.model", model)
                span.set_attribute("langfuse.model.unit", "TOKENS")
                span.set_attribute("langfuse.model.input_price", self.provider_pricing["openai_gpt4_mini_input"])
                span.set_attribute("langfuse.model.output_price", self.provider_pricing["openai_gpt4_mini_output"])

                # Add speech context if available
                if speech_id:
                    span.set_attribute("speech.id", speech_id)
                else:
                    span.set_attribute("speech.id", "no_speech_id")

                logger.debug(
                    f"LLM cost tracked: ${total_cost:.6f} "
                    f"(prompt: {prompt_tokens}, completion: {completion_tokens})"
                )
        except Exception as e:
            logger.warning(f"Failed to report LLM cost to Langfuse: {e}")

        return total_cost

    def track_stt_cost(
        self,
        audio_duration_seconds: float,
        provider: str = "deepgram",
        model: str = "nova-2",
        speech_id: Optional[str] = None
    ) -> float:
        """
        Track STT usage and costs, reporting to Langfuse.

        Args:
            audio_duration_seconds: Duration of audio processed
            provider: STT provider (deepgram, assemblyai)
            model: Model name
            speech_id: Optional speech turn identifier

        Returns:
            Total cost for this STT processing
        """
        # Determine pricing based on provider
        if provider == "deepgram":
            price_per_minute = self.provider_pricing["deepgram_nova2"]
        elif provider == "assemblyai":
            price_per_minute = self.provider_pricing["assemblyai_universal"]
        else:
            logger.warning(f"Unknown STT provider: {provider}, using Deepgram pricing")
            price_per_minute = self.provider_pricing["deepgram_nova2"]

        # Calculate cost
        minutes = audio_duration_seconds / 60.0
        total_cost = minutes * price_per_minute

        # Update session totals
        self.session_costs["stt"]["minutes"] += minutes
        self.session_costs["stt"]["cost"] += total_cost
        self.session_costs["total"] += total_cost

        # Report to Langfuse via OpenTelemetry span
        try:
            with self.tracer.start_as_current_span("stt_usage") as span:
                # Set Langfuse cost attributes
                span.set_attribute("langfuse.cost.total", total_cost)

                # Set usage details
                span.set_attribute("langfuse.usage.audio_seconds", audio_duration_seconds)
                span.set_attribute("langfuse.usage.audio_minutes", minutes)

                # Set model information
                span.set_attribute("langfuse.model", f"{provider}_{model}")
                span.set_attribute("langfuse.model.unit", "MINUTES")
                span.set_attribute("langfuse.model.price_per_minute", price_per_minute)

                # Add provider context
                span.set_attribute("stt.provider", provider)
                span.set_attribute("stt.model", model)

                # Add speech context if available
                if speech_id:
                    span.set_attribute("speech.id", speech_id)
                else:
                    span.set_attribute("speech.id", "no_speech_id")

                logger.debug(
                    f"STT cost tracked: ${total_cost:.6f} "
                    f"({minutes:.2f} minutes of {provider}/{model})"
                )
        except Exception as e:
            logger.warning(f"Failed to report STT cost to Langfuse: {e}")

        return total_cost

    def track_tts_cost(
        self,
        character_count: int,
        provider: str = "cartesia",
        model: str = "sonic-3",
        speech_id: Optional[str] = None
    ) -> float:
        """
        Track TTS usage and costs, reporting to Langfuse.

        Args:
            character_count: Number of characters synthesized
            provider: TTS provider (cartesia, elevenlabs)
            model: Model name
            speech_id: Optional speech turn identifier

        Returns:
            Total cost for this TTS generation
        """
        # Determine pricing based on provider
        if provider == "cartesia":
            price_per_char = self.provider_pricing["cartesia_sonic"]
        elif provider == "elevenlabs":
            price_per_char = self.provider_pricing["elevenlabs_turbo"] / 1000  # Convert from per 1K to per char
        else:
            logger.warning(f"Unknown TTS provider: {provider}, using Cartesia pricing")
            price_per_char = self.provider_pricing["cartesia_sonic"]

        # Calculate cost
        total_cost = character_count * price_per_char

        # Update session totals
        self.session_costs["tts"]["characters"] += character_count
        self.session_costs["tts"]["cost"] += total_cost
        self.session_costs["total"] += total_cost

        # Report to Langfuse via OpenTelemetry span
        try:
            with self.tracer.start_as_current_span("tts_usage") as span:
                # Set Langfuse cost attributes
                span.set_attribute("langfuse.cost.total", total_cost)

                # Set usage details
                span.set_attribute("langfuse.usage.characters", character_count)

                # Set model information
                span.set_attribute("langfuse.model", f"{provider}_{model}")
                span.set_attribute("langfuse.model.unit", "CHARACTERS")
                span.set_attribute("langfuse.model.price_per_character", price_per_char)

                # Add provider context
                span.set_attribute("tts.provider", provider)
                span.set_attribute("tts.model", model)

                # Add speech context if available
                if speech_id:
                    span.set_attribute("speech.id", speech_id)
                else:
                    span.set_attribute("speech.id", "no_speech_id")

                logger.debug(
                    f"TTS cost tracked: ${total_cost:.6f} "
                    f"({character_count} characters of {provider}/{model})"
                )
        except Exception as e:
            logger.warning(f"Failed to report TTS cost to Langfuse: {e}")

        return total_cost

    def track_conversation_turn(
        self,
        speech_id: str,
        stt_duration: Optional[float] = None,
        llm_prompt_tokens: Optional[int] = None,
        llm_completion_tokens: Optional[int] = None,
        tts_characters: Optional[int] = None,
        total_latency: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Track costs for an entire conversation turn, aggregating all model usage.

        This is useful for tracking costs at the conversation turn level,
        providing a complete picture of costs per user interaction.

        Args:
            speech_id: Unique identifier for this conversation turn
            stt_duration: Audio duration in seconds (if STT was used)
            llm_prompt_tokens: Input tokens (if LLM was used)
            llm_completion_tokens: Output tokens (if LLM was used)
            tts_characters: Characters synthesized (if TTS was used)
            total_latency: End-to-end latency for the turn

        Returns:
            Dictionary with cost breakdown for the turn
        """
        turn_costs = {
            "speech_id": speech_id,
            "timestamp": datetime.now().isoformat(),
            "costs": {},
            "total": 0.0
        }

        # Track each component if provided
        if stt_duration is not None:
            stt_cost = self.track_stt_cost(stt_duration, speech_id=speech_id)
            turn_costs["costs"]["stt"] = stt_cost
            turn_costs["total"] += stt_cost

        if llm_prompt_tokens is not None and llm_completion_tokens is not None:
            llm_cost = self.track_llm_cost(
                llm_prompt_tokens,
                llm_completion_tokens,
                speech_id=speech_id
            )
            turn_costs["costs"]["llm"] = llm_cost
            turn_costs["total"] += llm_cost

        if tts_characters is not None:
            tts_cost = self.track_tts_cost(tts_characters, speech_id=speech_id)
            turn_costs["costs"]["tts"] = tts_cost
            turn_costs["total"] += tts_cost

        # Create aggregate span for the entire turn
        try:
            with self.tracer.start_as_current_span("conversation_turn") as span:
                span.set_attribute("speech.id", speech_id)
                span.set_attribute("langfuse.cost.total", turn_costs["total"])

                # Add individual cost breakdowns
                for model_type, cost in turn_costs["costs"].items():
                    span.set_attribute(f"langfuse.cost.{model_type}", cost)

                # Add latency if available
                if total_latency is not None:
                    span.set_attribute("latency.total", total_latency)
                    turn_costs["latency"] = total_latency

                logger.info(
                    f"Turn {speech_id} cost: ${turn_costs['total']:.6f} "
                    f"(STT: ${turn_costs['costs'].get('stt', 0):.6f}, "
                    f"LLM: ${turn_costs['costs'].get('llm', 0):.6f}, "
                    f"TTS: ${turn_costs['costs'].get('tts', 0):.6f})"
                )
        except Exception as e:
            logger.warning(f"Failed to report turn cost to Langfuse: {e}")

        return turn_costs

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all costs for the current session.

        Returns:
            Dictionary with complete cost breakdown
        """
        return {
            "llm": {
                "total_tokens": self.session_costs["llm"]["tokens"],
                "total_cost": self.session_costs["llm"]["cost"]
            },
            "stt": {
                "total_minutes": self.session_costs["stt"]["minutes"],
                "total_cost": self.session_costs["stt"]["cost"]
            },
            "tts": {
                "total_characters": self.session_costs["tts"]["characters"],
                "total_cost": self.session_costs["tts"]["cost"]
            },
            "total_cost": self.session_costs["total"],
            "timestamp": datetime.now().isoformat()
        }

    def report_session_summary(self) -> None:
        """Report final session cost summary to Langfuse."""
        summary = self.get_session_summary()

        try:
            with self.tracer.start_as_current_span("session_cost_summary") as span:
                # Report total cost
                span.set_attribute("langfuse.cost.total", summary["total_cost"])

                # Report individual model costs
                span.set_attribute("langfuse.cost.llm", summary["llm"]["total_cost"])
                span.set_attribute("langfuse.cost.stt", summary["stt"]["total_cost"])
                span.set_attribute("langfuse.cost.tts", summary["tts"]["total_cost"])

                # Report usage metrics
                span.set_attribute("langfuse.usage.llm_tokens", summary["llm"]["total_tokens"])
                span.set_attribute("langfuse.usage.stt_minutes", summary["stt"]["total_minutes"])
                span.set_attribute("langfuse.usage.tts_characters", summary["tts"]["total_characters"])

                logger.info(
                    f"Session cost summary: Total ${summary['total_cost']:.4f} "
                    f"(LLM: ${summary['llm']['total_cost']:.4f}, "
                    f"STT: ${summary['stt']['total_cost']:.4f}, "
                    f"TTS: ${summary['tts']['total_cost']:.4f})"
                )
        except Exception as e:
            logger.warning(f"Failed to report session summary to Langfuse: {e}")