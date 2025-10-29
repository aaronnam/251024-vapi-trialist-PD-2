"""
Telemetry and observability configuration for voice agent.
Provides OpenTelemetry tracing via LangFuse for debugging and performance monitoring.

Based on official LiveKit + Langfuse integration:
https://langfuse.com/integrations/frameworks/livekit
https://github.com/livekit/agents/blob/main/examples/voice_agents/langfuse_trace.py
"""

import base64
import logging
import os
from typing import Optional, Dict, Any

from livekit.agents.telemetry import set_tracer_provider

logger = logging.getLogger(__name__)


def setup_observability(metadata: Optional[Dict[str, Any]] = None):
    """
    Set up OpenTelemetry tracing with LangFuse.

    Args:
        metadata: Optional metadata to attach to all traces (e.g., session_id, user_id)
                 Common keys: "langfuse.session.id", "langfuse.user.id", "langfuse.metadata.*"

    Returns:
        TracerProvider if successfully configured, None otherwise.
        Gracefully handles missing configuration.

    Example:
        trace_provider = setup_observability(
            metadata={"langfuse.session.id": room_name}
        )
        if trace_provider:
            # Register shutdown callback to flush traces
            ctx.add_shutdown_callback(lambda: trace_provider.force_flush())
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # Check if tracing is configured
    if not public_key or not secret_key:
        logger.info(
            "Tracing not configured (missing LANGFUSE keys). "
            "Running without tracing. To enable, set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY."
        )
        return None

    try:
        # Import OpenTelemetry components
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource

        # Configure LangFuse authentication
        langfuse_auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()

        # Set OTLP endpoint and headers for LangFuse
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{host.rstrip('/')}/api/public/otel"
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {langfuse_auth}"

        # Create resource with service name and metadata
        resource_attrs = {
            "service.name": "pandadoc-voice-agent",
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("DEPLOYMENT_ENV", "production"),
        }

        # Add custom metadata if provided
        if metadata:
            resource_attrs.update(metadata)

        resource = Resource.create(resource_attrs)

        # Configure tracer provider with resource
        trace_provider = TracerProvider(resource=resource)

        # Add batch span processor for efficient export
        trace_provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(),
                max_queue_size=2048,
                max_export_batch_size=512,
            )
        )

        # Set as the global tracer provider with metadata
        set_tracer_provider(trace_provider, metadata=metadata)

        logger.info(
            f"✅ Tracing enabled with LangFuse at {host}. "
            f"View traces at: {host}/project/{public_key.split('-')[0] if '-' in public_key else 'default'}"
        )
        return trace_provider

    except Exception as e:
        logger.error(f"Failed to set up tracing: {e}")
        return None


def create_custom_span(name: str, attributes: Optional[dict] = None):
    """
    Helper to create custom spans for specific operations.

    Args:
        name: Name of the span
        attributes: Optional attributes to add to the span

    Example:
        with create_custom_span("database_query", {"query": "SELECT ..."}):
            # Your code here
            pass
    """
    try:
        from opentelemetry import trace

        tracer = trace.get_tracer(__name__)
        span = tracer.start_span(name)

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))

        return span
    except:
        # Return a no-op context manager if tracing not available
        class NoOpSpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return NoOpSpan()