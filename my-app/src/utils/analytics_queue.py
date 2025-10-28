"""
Analytics Queue Utility

Sends session data to analytics queue for asynchronous processing.
This follows the separated architecture pattern:
- LiveKit agent collects data (lightweight, 0ms latency impact)
- Analytics service processes data (heavy LLM analysis, async)

For LiveKit Cloud deployments:
- Uses structured JSON logging for CloudWatch ingestion
- Logs are automatically forwarded when AWS credentials are configured
- Query analytics data using CloudWatch Insights
"""

import json
import logging
import os
from typing import Any, Dict

# Standard logger for debug messages
logger = logging.getLogger("analytics_queue")


# Structured JSON formatter for analytics events
class StructuredAnalyticsFormatter(logging.Formatter):
    """Formats analytics data as structured JSON for CloudWatch."""

    def format(self, record):
        if hasattr(record, 'analytics_data'):
            # This is an analytics event - format as structured JSON
            analytics_json = {
                "_event_type": "session_analytics",
                "_timestamp": record.created,
                "_log_level": record.levelname,
                **record.analytics_data
            }
            # Add session_id at top level for easier CloudWatch queries
            if 'session_id' in record.analytics_data:
                analytics_json['_session_id'] = record.analytics_data['session_id']
            return json.dumps(analytics_json)
        # Regular log message
        return super().format(record)


# Create dedicated analytics logger with structured output
analytics_logger = logging.getLogger("livekit.analytics")
analytics_handler = logging.StreamHandler()
analytics_handler.setFormatter(StructuredAnalyticsFormatter())
analytics_logger.addHandler(analytics_handler)
analytics_logger.setLevel(logging.INFO)


async def send_to_analytics_queue(data: Dict[str, Any]) -> None:
    """Send session data to analytics queue.

    Args:
        data: Complete session data payload including:
            - session_id: Unique session identifier
            - start_time/end_time: Session timestamps
            - discovered_signals: Business qualification signals
            - tool_calls: Tool usage tracking
            - metrics_summary: LiveKit performance metrics
            - conversation_notes: Free-form notes

    LiveKit Cloud Implementation:
        - Logs as structured JSON for CloudWatch ingestion
        - Automatically forwarded when AWS credentials are configured
        - Queryable via CloudWatch Insights

    To enable CloudWatch forwarding in LiveKit Cloud:
        ```bash
        lk agent update-secrets \
          --secrets "AWS_ACCESS_KEY_ID=your-key-id" \
          --secrets "AWS_SECRET_ACCESS_KEY=your-secret" \
          --secrets "AWS_REGION=us-east-1"
        ```

    CloudWatch Insights query examples:
        ```sql
        -- Find all analytics events
        fields @timestamp, _session_id, duration_seconds, discovered_signals
        | filter _event_type = "session_analytics"
        | sort @timestamp desc

        -- Get qualified leads
        fields _session_id, discovered_signals.team_size
        | filter _event_type = "session_analytics"
        | filter discovered_signals.team_size >= 5
        ```
    """
    try:
        # Validate data is JSON serializable
        json.dumps(data)  # Will raise TypeError if not serializable

        # Log as structured JSON for CloudWatch
        # This will be automatically forwarded if AWS credentials are configured
        analytics_logger.info(
            "Session analytics data",
            extra={"analytics_data": data}
        )

        # Also log summary for debugging (standard format)
        logger.info(f"Analytics data exported for session: {data.get('session_id')}")
        logger.debug(f"  Duration: {data.get('duration_seconds', 0):.1f}s")
        logger.debug(f"  Tool Calls: {len(data.get('tool_calls', []))}")
        logger.debug(f"  Qualification: {data.get('discovered_signals', {}).get('qualification_tier', 'Unknown')}")

        # Calculate some key metrics for summary logging
        team_size = data.get('discovered_signals', {}).get('team_size', 0)
        monthly_volume = data.get('discovered_signals', {}).get('monthly_volume', 0)
        is_qualified = team_size >= 5 or monthly_volume >= 100

        if is_qualified:
            # Log hot leads with higher visibility
            logger.info(
                f"🔥 HOT LEAD - Session {data.get('session_id')}: "
                f"Team size {team_size}, Volume {monthly_volume}/month"
            )

    except TypeError as e:
        logger.error(f"Analytics data is not JSON serializable: {e}")
        raise

    except Exception as e:
        # Fail gracefully - analytics errors shouldn't crash the agent
        logger.error(f"Failed to send analytics data: {e}", exc_info=True)


# Environment variable documentation for Phase 2
REQUIRED_ENV_VARS = {
    "google_pubsub": [
        "GCP_PROJECT_ID",  # Google Cloud project ID
        "ANALYTICS_TOPIC",  # Pub/Sub topic name (default: voice-sessions)
        "GOOGLE_APPLICATION_CREDENTIALS",  # Path to service account JSON (optional, uses default credentials if not set)
    ],
    "aws_sqs": [
        "AWS_REGION",  # AWS region (e.g., us-east-1)
        "ANALYTICS_QUEUE_URL",  # Full SQS queue URL
        "AWS_ACCESS_KEY_ID",  # AWS access key (optional, uses IAM role if not set)
        "AWS_SECRET_ACCESS_KEY",  # AWS secret key (optional, uses IAM role if not set)
    ],
}
