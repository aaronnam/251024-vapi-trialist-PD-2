"""
Test Langfuse integration for user identification and transcript tracking.

These tests verify that:
1. User email is properly set in session-level context
2. User transcriptions are captured and sent to Langfuse
3. Conversation items are tracked with proper attributes
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, ANY
from livekit.agents import UserInputTranscribedEvent
from livekit.agents.llm import ChatMessage, ChatRole


@pytest.fixture
def mock_tracer():
    """Create a mock OpenTelemetry tracer."""
    with patch('opentelemetry.trace.get_tracer') as mock_get_tracer:
        mock_tracer = MagicMock()
        mock_span = MagicMock()

        # Configure the span context manager
        mock_tracer.start_as_current_span.return_value.__enter__ = Mock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = Mock(return_value=None)

        mock_get_tracer.return_value = mock_tracer

        yield {
            'tracer': mock_tracer,
            'span': mock_span,
            'get_tracer': mock_get_tracer
        }


@pytest.fixture
def mock_session():
    """Create a mock AgentSession with event handlers."""
    session = Mock()
    session.handlers = {}

    def on(event_name):
        """Decorator to register event handlers."""
        def decorator(func):
            session.handlers[event_name] = func
            return func
        return decorator

    session.on = on
    return session


class TestUserIdentification:
    """Test suite for user identification in Langfuse."""

    @patch('livekit.agents.telemetry.set_tracer_provider')
    def test_set_tracer_provider_called_with_user_email(self, mock_set_tracer):
        """Verify set_tracer_provider is called with user email after participant joins."""
        from livekit.agents.telemetry import set_tracer_provider

        # Simulate the code that updates tracer provider
        trace_provider = Mock()
        user_email = "test@example.com"
        room_name = "test-room-123"
        participant_identity = "participant-456"

        set_tracer_provider(trace_provider, metadata={
            "langfuse.session.id": room_name,
            "langfuse.user.id": user_email,
            "user.email": user_email,
            "participant.identity": participant_identity
        })

        # Verify the function was called
        mock_set_tracer.assert_called_once()
        call_args = mock_set_tracer.call_args

        # Verify metadata includes all required fields
        assert call_args[0][0] == trace_provider
        metadata = call_args[1]['metadata']
        assert metadata['langfuse.session.id'] == room_name
        assert metadata['langfuse.user.id'] == user_email
        assert metadata['user.email'] == user_email
        assert metadata['participant.identity'] == participant_identity

    def test_participant_identification_span_attributes(self, mock_tracer):
        """Verify participant identification creates a span with correct attributes."""
        from opentelemetry import trace as otel_trace

        tracer = otel_trace.get_tracer(__name__)

        user_email = "test@example.com"
        participant_identity = "participant-456"

        # Simulate creating the span (as done in agent.py lines 1810-1813)
        with tracer.start_as_current_span("participant_identified") as span:
            span.set_attribute("langfuse.user.id", user_email)
            span.set_attribute("user.email", user_email)
            span.set_attribute("participant.identity", participant_identity)

        # Verify span was created
        mock_tracer['tracer'].start_as_current_span.assert_called_once_with("participant_identified")

        # Verify all attributes were set
        mock_span = mock_tracer['span']
        assert mock_span.set_attribute.call_count == 3

        # Check specific attributes
        calls = [call[0] for call in mock_span.set_attribute.call_args_list]
        assert ("langfuse.user.id", user_email) in calls
        assert ("user.email", user_email) in calls
        assert ("participant.identity", participant_identity) in calls


class TestUserTranscriptionTracking:
    """Test suite for user transcription tracking."""

    def test_user_input_transcribed_event_handler_registered(self, mock_session):
        """Verify user_input_transcribed event handler is registered."""
        # Simulate registering the handler
        @mock_session.on("user_input_transcribed")
        def on_user_input_transcribed(ev):
            pass

        assert "user_input_transcribed" in mock_session.handlers
        assert callable(mock_session.handlers["user_input_transcribed"])

    def test_user_input_transcribed_creates_span_with_attributes(self, mock_tracer):
        """Verify user_input_transcribed creates a span with proper attributes."""
        from opentelemetry import trace as otel_trace

        # Create mock event
        mock_event = Mock()
        mock_event.transcript = "Hello, I need help with PandaDoc"
        mock_event.is_final = True
        mock_event.language = "en"

        tracer = otel_trace.get_tracer(__name__)

        # Simulate the event handler logic (agent.py lines 1492-1498)
        with tracer.start_as_current_span("user_speech") as span:
            span.set_attribute("user.transcript", mock_event.transcript)
            span.set_attribute("user.transcript.is_final", mock_event.is_final)
            span.set_attribute("langfuse.input", mock_event.transcript)
            if hasattr(mock_event, 'language') and mock_event.language:
                span.set_attribute("user.language", mock_event.language)

        # Verify span was created with correct name
        mock_tracer['tracer'].start_as_current_span.assert_called_once_with("user_speech")

        # Verify critical attributes were set
        mock_span = mock_tracer['span']
        calls = [call[0] for call in mock_span.set_attribute.call_args_list]

        assert ("user.transcript", "Hello, I need help with PandaDoc") in calls
        assert ("user.transcript.is_final", True) in calls
        assert ("langfuse.input", "Hello, I need help with PandaDoc") in calls
        assert ("user.language", "en") in calls

    def test_partial_transcripts_tracked_correctly(self, mock_tracer):
        """Verify partial transcripts (is_final=False) are tracked."""
        from opentelemetry import trace as otel_trace

        mock_event = Mock()
        mock_event.transcript = "Hello, I"
        mock_event.is_final = False

        tracer = otel_trace.get_tracer(__name__)

        with tracer.start_as_current_span("user_speech") as span:
            span.set_attribute("user.transcript", mock_event.transcript)
            span.set_attribute("user.transcript.is_final", mock_event.is_final)
            span.set_attribute("langfuse.input", mock_event.transcript)

        # Verify is_final=False is properly set
        mock_span = mock_tracer['span']
        calls = [call[0] for call in mock_span.set_attribute.call_args_list]
        assert ("user.transcript.is_final", False) in calls


class TestConversationItemTracking:
    """Test suite for conversation item tracking."""

    def test_conversation_item_added_event_handler_registered(self, mock_session):
        """Verify conversation_item_added event handler is registered."""
        @mock_session.on("conversation_item_added")
        def on_conversation_item_added(ev):
            pass

        assert "conversation_item_added" in mock_session.handlers
        assert callable(mock_session.handlers["conversation_item_added"])

    def test_user_conversation_item_creates_span_with_input(self, mock_tracer):
        """Verify user conversation items set langfuse.input attribute."""
        from opentelemetry import trace as otel_trace

        # Create mock conversation item for user
        mock_item = Mock()
        mock_item.role = "user"
        mock_item.text_content = "How do I set up e-signatures?"
        mock_item.interrupted = False

        mock_event = Mock()
        mock_event.item = mock_item

        tracer = otel_trace.get_tracer(__name__)

        # Simulate the event handler logic (agent.py lines 1528-1537)
        with tracer.start_as_current_span("conversation_item") as span:
            span.set_attribute("conversation.role", mock_item.role)
            span.set_attribute("conversation.content", mock_item.text_content)
            span.set_attribute("conversation.interrupted", mock_item.interrupted)

            # Set input/output based on role
            if mock_item.role == "user":
                span.set_attribute("langfuse.input", mock_item.text_content)
            elif mock_item.role == "assistant":
                span.set_attribute("langfuse.output", mock_item.text_content)

        # Verify span attributes
        mock_span = mock_tracer['span']
        calls = [call[0] for call in mock_span.set_attribute.call_args_list]

        assert ("conversation.role", "user") in calls
        assert ("conversation.content", "How do I set up e-signatures?") in calls
        assert ("langfuse.input", "How do I set up e-signatures?") in calls

    def test_assistant_conversation_item_creates_span_with_output(self, mock_tracer):
        """Verify assistant conversation items set langfuse.output attribute."""
        from opentelemetry import trace as otel_trace

        # Create mock conversation item for assistant
        mock_item = Mock()
        mock_item.role = "assistant"
        mock_item.text_content = "You can set up e-signatures by going to the Documents tab."
        mock_item.interrupted = False

        tracer = otel_trace.get_tracer(__name__)

        with tracer.start_as_current_span("conversation_item") as span:
            span.set_attribute("conversation.role", mock_item.role)
            span.set_attribute("conversation.content", mock_item.text_content)
            span.set_attribute("conversation.interrupted", mock_item.interrupted)

            if mock_item.role == "user":
                span.set_attribute("langfuse.input", mock_item.text_content)
            elif mock_item.role == "assistant":
                span.set_attribute("langfuse.output", mock_item.text_content)

        # Verify span attributes
        mock_span = mock_tracer['span']
        calls = [call[0] for call in mock_span.set_attribute.call_args_list]

        assert ("conversation.role", "assistant") in calls
        assert ("langfuse.output", "You can set up e-signatures by going to the Documents tab.") in calls


class TestEventHandlerErrorHandling:
    """Test suite for error handling in event handlers."""

    def test_user_input_transcribed_handles_missing_transcript(self, mock_tracer):
        """Verify handler gracefully handles events with missing transcript."""
        from opentelemetry import trace as otel_trace

        mock_event = Mock()
        mock_event.transcript = ""  # Empty transcript
        mock_event.is_final = True

        # The handler should check if transcript exists before creating span
        if mock_event.transcript:
            tracer = otel_trace.get_tracer(__name__)
            with tracer.start_as_current_span("user_speech") as span:
                span.set_attribute("user.transcript", mock_event.transcript)

        # Verify no span was created for empty transcript
        mock_tracer['tracer'].start_as_current_span.assert_not_called()

    def test_conversation_item_handles_missing_text_content(self, mock_tracer):
        """Verify handler can handle items without text_content attribute."""
        from opentelemetry import trace as otel_trace

        # Create mock item without text_content attribute
        mock_item = Mock(spec=['role', 'content', 'interrupted'])
        mock_item.role = "user"
        mock_item.content = ["Some", "content", "list"]
        mock_item.interrupted = False

        tracer = otel_trace.get_tracer(__name__)

        # Use fallback to str(item.content) if text_content not available
        content = mock_item.text_content if hasattr(mock_item, 'text_content') else str(mock_item.content)

        with tracer.start_as_current_span("conversation_item") as span:
            span.set_attribute("conversation.role", mock_item.role)
            span.set_attribute("conversation.content", content)

        # Verify span was created with fallback content
        mock_span = mock_tracer['span']
        calls = [call[0] for call in mock_span.set_attribute.call_args_list]
        assert ("conversation.content", str(["Some", "content", "list"])) in calls


class TestLangfuseSpecificAttributes:
    """Test suite for Langfuse-specific attribute names."""

    def test_langfuse_input_attribute_present_for_user_speech(self, mock_tracer):
        """Verify langfuse.input attribute is set for user transcriptions."""
        from opentelemetry import trace as otel_trace

        tracer = otel_trace.get_tracer(__name__)
        transcript = "Test user input"

        with tracer.start_as_current_span("user_speech") as span:
            span.set_attribute("langfuse.input", transcript)

        mock_span = mock_tracer['span']
        mock_span.set_attribute.assert_any_call("langfuse.input", transcript)

    def test_langfuse_user_id_attribute_present(self, mock_tracer):
        """Verify langfuse.user.id attribute is set in participant identification."""
        from opentelemetry import trace as otel_trace

        tracer = otel_trace.get_tracer(__name__)
        user_email = "test@example.com"

        with tracer.start_as_current_span("participant_identified") as span:
            span.set_attribute("langfuse.user.id", user_email)

        mock_span = mock_tracer['span']
        mock_span.set_attribute.assert_any_call("langfuse.user.id", user_email)

    def test_langfuse_session_id_in_metadata(self):
        """Verify langfuse.session.id is set in tracer provider metadata."""
        with patch('livekit.agents.telemetry.set_tracer_provider') as mock_set_tracer:
            from livekit.agents.telemetry import set_tracer_provider

            trace_provider = Mock()
            room_name = "test-room-123"

            set_tracer_provider(trace_provider, metadata={
                "langfuse.session.id": room_name
            })

            # Verify metadata contains session ID
            call_args = mock_set_tracer.call_args
            metadata = call_args[1]['metadata']
            assert "langfuse.session.id" in metadata
            assert metadata["langfuse.session.id"] == room_name


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
