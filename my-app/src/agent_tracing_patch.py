"""
INTEGRATION INSTRUCTIONS FOR TRACING AND ENHANCED METRICS

Add the following changes to your agent.py file:

1. Add imports at the top (around line 30):
"""

# Add these imports after the existing imports
from livekit.agents import MetricsCollectedEvent
from utils.telemetry import setup_observability, create_custom_span
from utils.analytics_queue import analytics_logger

"""
2. In the entrypoint function, right after ctx.log_context_fields (around line 1103):
"""

async def entrypoint(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # ADD THIS: Initialize observability and tracing
    tracing_enabled = setup_observability()
    logger.info(f"Starting session {ctx.room.name} - Tracing: {'enabled' if tracing_enabled else 'disabled'}")

"""
3. In PandaDocVoiceAgent.__init__, after self.usage_collector (around line 248):
"""

        self.usage_collector = metrics.UsageCollector()  # LiveKit built-in metrics

        # ADD THIS: Track detailed metrics
        self.metrics_buffer = []
        self.latency_warnings = []

"""
4. After the AgentSession is created (around line 1150), add metrics handler:
"""

    # Create the agent
    agent_instance = PandaDocVoiceAgent(room_name=ctx.room.name)
    session.set_agent(agent_instance)

    # ADD THIS: Enhanced metrics collection
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        """Capture and analyze real-time performance metrics."""
        # Log metrics for immediate visibility
        metrics.log_metrics(ev.metrics)

        # Also collect for aggregation
        agent_instance.usage_collector.collect(ev.metrics)

        # Build structured metric data for CloudWatch
        if ev.metrics:
            metric_data = {
                "_event_type": "voice_metrics",
                "_timestamp": datetime.now().isoformat(),
                "_session_id": ctx.room.name,
                "_room_name": ctx.room.name,
            }

            # Extract specific metrics
            if ev.metrics.llm:
                metric_data["llm"] = {
                    "ttft": ev.metrics.llm.ttft,
                    "duration": ev.metrics.llm.duration,
                    "tokens_per_second": ev.metrics.llm.tokens_per_second,
                    "prompt_tokens": ev.metrics.llm.prompt_tokens,
                    "completion_tokens": ev.metrics.llm.completion_tokens,
                    "total_tokens": ev.metrics.llm.total_tokens,
                }

            if ev.metrics.tts:
                metric_data["tts"] = {
                    "ttfb": ev.metrics.tts.ttfb,
                    "duration": ev.metrics.tts.duration,
                    "audio_duration": ev.metrics.tts.audio_duration,
                    "characters": ev.metrics.tts.characters_count,
                }

            if ev.metrics.stt:
                metric_data["stt"] = {
                    "duration": ev.metrics.stt.duration,
                    "audio_duration": ev.metrics.stt.audio_duration,
                    "streamed": ev.metrics.stt.streamed,
                }

            if ev.metrics.eou:
                metric_data["eou"] = {
                    "delay": ev.metrics.eou.end_of_utterance_delay,
                    "transcription_delay": ev.metrics.eou.transcription_delay,
                }

                # Calculate total latency (the key metric)
                if ev.metrics.llm and ev.metrics.tts:
                    total_latency = (
                        ev.metrics.eou.end_of_utterance_delay +
                        (ev.metrics.llm.ttft or 0) +
                        (ev.metrics.tts.ttfb or 0)
                    )
                    metric_data["total_latency"] = total_latency

                    # Alert on high latency
                    if total_latency > 1.5:
                        logger.warning(
                            f"⚠️ High latency detected: {total_latency:.2f}s "
                            f"(EOU: {ev.metrics.eou.end_of_utterance_delay:.2f}s, "
                            f"LLM: {ev.metrics.llm.ttft:.2f}s, "
                            f"TTS: {ev.metrics.tts.ttfb:.2f}s)"
                        )
                        agent_instance.latency_warnings.append({
                            "timestamp": datetime.now().isoformat(),
                            "total_latency": total_latency,
                            "breakdown": {
                                "eou": ev.metrics.eou.end_of_utterance_delay,
                                "llm_ttft": ev.metrics.llm.ttft,
                                "tts_ttfb": ev.metrics.tts.ttfb,
                            }
                        })

            # Store in buffer for session summary
            agent_instance.metrics_buffer.append(metric_data)

            # Log to CloudWatch as structured JSON
            analytics_logger.info(
                "Voice metrics collected",
                extra={"analytics_data": metric_data}
            )

"""
5. Enhance the shutdown callback to include metrics summary (around line 1160):
"""

    async def export_session_data():
        """Export session data to analytics queue on shutdown."""
        try:
            # ... existing code ...

            # ADD THIS: Include latency analysis
            if agent_instance.metrics_buffer:
                latencies = [
                    m.get("total_latency")
                    for m in agent_instance.metrics_buffer
                    if m.get("total_latency") is not None
                ]

                if latencies:
                    import statistics
                    session_payload["latency_analysis"] = {
                        "avg": statistics.mean(latencies),
                        "p95": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0],
                        "max": max(latencies),
                        "warnings_count": len(agent_instance.latency_warnings),
                        "warnings": agent_instance.latency_warnings[:5],  # First 5 warnings
                    }

"""
6. Add custom spans for critical operations (in unleash_search_knowledge, around line 440):
"""

    async def unleash_search_knowledge(
        self, context: RunContext, query: str, category: Optional[str] = None
    ) -> str:
        # ADD THIS: Create span for tracking search performance
        with create_custom_span(
            "unleash_search",
            {"query": query, "category": category or "all"}
        ):
            # ... existing search code ...

"""
7. Add custom spans for booking tool (in book_sales_meeting, around line 860):
"""

    async def book_sales_meeting(
        self,
        context: RunContext,
        customer_name: str,
        customer_email: str,
        preferred_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        # ADD THIS: Create span for tracking booking performance
        with create_custom_span(
            "book_meeting",
            {
                "qualified": self.should_route_to_sales(),
                "has_date_pref": bool(preferred_date),
                "has_time_pref": bool(preferred_time),
            }
        ):
            # ... existing booking code ...