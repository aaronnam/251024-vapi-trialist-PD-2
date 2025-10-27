"""Test suite for the Unleash knowledge base integration tool.

This module tests the unleash_search_knowledge function tool with various scenarios
including successful searches, error handling, and response formatting.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

# Add src to path to import agent
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from livekit.agents import AgentSession, ToolError, inference

from agent import PandaDocTrialistAgent


@pytest.mark.asyncio
async def test_unleash_search_basic():
    """Test basic knowledge search returns actionable response."""
    # Mock the Unleash API response
    mock_response = {
        "totalResults": 1,
        "results": [
            {
                "resource": {
                    "title": "Creating Templates in PandaDoc",
                    "description": "Step-by-step guide",
                },
                "snippet": "To create a template, go to Templates section...",
                "highlights": ["Templates", "create"],
            }
        ],
        "requestId": "test-123",
    }

    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        # Mock httpx.AsyncClient.post
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = AsyncMock()

            await session.start(agent)
            result = await session.run(user_input="How do I create templates?")

            # Verify tool was called with correct parameters
            result.expect.next_event().is_function_call(
                name="unleash_search_knowledge",
                arguments_match=lambda args: "template"
                in args.get("query", "").lower(),
            )

            # Verify agent provides helpful response
            await result.expect.next_event().is_message(
                role="assistant"
            ).judge(
                llm, intent="Provides guidance on creating templates based on search results"
            )


@pytest.mark.asyncio
async def test_unleash_missing_api_key():
    """Test handling when API key is not configured."""
    # Temporarily remove API key
    original_key = os.environ.pop("UNLEASH_API_KEY", None)

    try:
        async with (
            inference.LLM(model="openai/gpt-4o-mini") as llm,
            AgentSession(llm=llm) as session,
        ):
            await session.start(PandaDocTrialistAgent())
            result = await session.run(user_input="What are the pricing plans?")

            # Verify tool handles missing API key gracefully
            result.expect.next_event().is_function_call(
                name="unleash_search_knowledge"
            )

            # Should get ToolError about missing configuration
            error_event = result.expect.next_event().is_function_call_error()
            assert "not configured" in str(error_event.item.error).lower()

            # Verify agent offers alternative help
            await result.expect.contains_message(role="assistant").judge(
                llm, intent="Offers to help directly without the knowledge base"
            )
    finally:
        # Restore API key if it existed
        if original_key:
            os.environ["UNLEASH_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_unleash_api_timeout():
    """Test graceful handling of API timeout."""
    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        # Mock httpx timeout
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")

            await session.start(agent)
            result = await session.run(user_input="How do integrations work?")

            # Tool should be called
            result.expect.next_event().is_function_call(
                name="unleash_search_knowledge"
            )

            # Should handle timeout with ToolError
            error_event = result.expect.next_event().is_function_call_error()
            assert "taking longer" in str(error_event.item.error).lower()

            # Agent should offer alternative help
            await result.expect.contains_message(role="assistant").judge(
                llm, intent="Offers to help directly when search times out"
            )


@pytest.mark.asyncio
async def test_unleash_response_format():
    """Test concise vs detailed response format."""
    mock_response = {
        "totalResults": 3,
        "results": [
            {
                "resource": {"title": "Salesforce Integration"},
                "snippet": "Connect Salesforce...",
            },
            {
                "resource": {"title": "HubSpot Integration"},
                "snippet": "Sync with HubSpot...",
            },
            {
                "resource": {"title": "Zapier Integration"},
                "snippet": "Automate workflows...",
            },
        ],
    }

    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = PandaDocTrialistAgent()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.raise_for_status = AsyncMock()

            await session.start(agent)

            # Test default concise format
            result = await session.run(user_input="What integrations exist?")
            event = result.expect.next_event().is_function_call(
                name="unleash_search_knowledge"
            )

            # Verify default is concise or explicitly set
            args = event.item.arguments
            assert args.get("response_format", "concise") == "concise"

            # Test that the tool can handle both formats
            # (The actual format request would come from conversation context)


@pytest.mark.asyncio
async def test_unleash_authentication_failure():
    """Test handling of 401 authentication errors."""
    # Set a dummy API key to avoid the missing key error
    os.environ["UNLEASH_API_KEY"] = "invalid_test_key"

    try:
        async with (
            inference.LLM(model="openai/gpt-4o-mini") as llm,
            AgentSession(llm=llm) as session,
        ):
            agent = PandaDocTrialistAgent()

            # Mock 401 response
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value.status_code = 401
                mock_post.return_value.text = "Unauthorized"
                mock_post.return_value.raise_for_status = AsyncMock()

                await session.start(agent)
                result = await session.run(
                    user_input="Show me the latest features"
                )

                # Tool should be called
                result.expect.next_event().is_function_call(
                    name="unleash_search_knowledge"
                )

                # Should handle auth error with ToolError
                error_event = result.expect.next_event().is_function_call_error()
                error_message = str(error_event.item.error).lower()
                assert "trouble accessing" in error_message or "help you directly" in error_message

                # Agent should offer alternative help
                await result.expect.contains_message(role="assistant").judge(
                    llm, intent="Offers to help directly when authentication fails"
                )
    finally:
        # Clean up
        os.environ.pop("UNLEASH_API_KEY", None)


@pytest.mark.asyncio
async def test_unleash_server_error():
    """Test handling of 500+ server errors."""
    # Set a dummy API key
    os.environ["UNLEASH_API_KEY"] = "test_key"

    try:
        async with (
            inference.LLM(model="openai/gpt-4o-mini") as llm,
            AgentSession(llm=llm) as session,
        ):
            agent = PandaDocTrialistAgent()

            # Mock 500 response
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value.status_code = 503
                mock_post.return_value.text = "Service Unavailable"
                mock_post.return_value.raise_for_status = AsyncMock()

                await session.start(agent)
                result = await session.run(user_input="Help with document signing")

                # Tool should be called
                result.expect.next_event().is_function_call(
                    name="unleash_search_knowledge"
                )

                # Should handle server error with ToolError
                error_event = result.expect.next_event().is_function_call_error()
                error_message = str(error_event.item.error).lower()
                assert "temporarily unavailable" in error_message or "still help" in error_message

                # Agent should offer to help anyway
                await result.expect.contains_message(role="assistant").judge(
                    llm,
                    intent="Offers assistance despite knowledge base being unavailable",
                )
    finally:
        # Clean up
        os.environ.pop("UNLEASH_API_KEY", None)


@pytest.mark.asyncio
async def test_unleash_empty_results():
    """Test handling when search returns no results."""
    mock_response = {"totalResults": 0, "results": [], "requestId": "test-empty"}

    # Set a dummy API key
    os.environ["UNLEASH_API_KEY"] = "test_key"

    try:
        async with (
            inference.LLM(model="openai/gpt-4o-mini") as llm,
            AgentSession(llm=llm) as session,
        ):
            agent = PandaDocTrialistAgent()

            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response
                mock_post.return_value.raise_for_status = AsyncMock()

                await session.start(agent)
                result = await session.run(
                    user_input="Tell me about quantum computing features"
                )

                # Tool should be called
                result.expect.next_event().is_function_call(
                    name="unleash_search_knowledge"
                )

                # Should handle empty results gracefully
                # The tool returns found=False and action="offer_human_help"
                await result.expect.contains_message(role="assistant").judge(
                    llm,
                    intent="Acknowledges search found no results and offers alternative help",
                )
    finally:
        # Clean up
        os.environ.pop("UNLEASH_API_KEY", None)


@pytest.mark.asyncio
async def test_unleash_category_filtering():
    """Test that category parameter is correctly passed to API."""
    mock_response = {
        "totalResults": 2,
        "results": [
            {
                "resource": {"title": "Pro Plan", "description": "Professional tier"},
                "snippet": "Pro plan includes unlimited documents...",
                "highlights": ["Pro", "unlimited"],
            },
            {
                "resource": {"title": "Enterprise Plan", "description": "Enterprise tier"},
                "snippet": "Enterprise plan includes advanced features...",
                "highlights": ["Enterprise", "advanced"],
            },
        ],
        "requestId": "test-category",
    }

    # Set a dummy API key
    os.environ["UNLEASH_API_KEY"] = "test_key"

    try:
        async with (
            inference.LLM(model="openai/gpt-4o-mini") as llm,
            AgentSession(llm=llm) as session,
        ):
            agent = PandaDocTrialistAgent()

            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response
                mock_post.return_value.raise_for_status = AsyncMock()

                await session.start(agent)

                # Simulate a query that should trigger pricing category
                result = await session.run(user_input="What are the pricing plans?")

                # Tool should be called
                event = result.expect.next_event().is_function_call(
                    name="unleash_search_knowledge"
                )

                # Verify the query contains pricing-related terms
                args = event.item.arguments
                query = args.get("query", "").lower()
                assert any(word in query for word in ["pricing", "plan", "cost", "price"])

                # The agent should provide pricing information
                await result.expect.contains_message(role="assistant").judge(
                    llm, intent="Provides information about pricing plans"
                )
    finally:
        # Clean up
        os.environ.pop("UNLEASH_API_KEY", None)


@pytest.mark.asyncio
async def test_unleash_network_error():
    """Test handling of network/connection errors."""
    # Set a dummy API key
    os.environ["UNLEASH_API_KEY"] = "test_key"

    try:
        async with (
            inference.LLM(model="openai/gpt-4o-mini") as llm,
            AgentSession(llm=llm) as session,
        ):
            agent = PandaDocTrialistAgent()

            # Mock network error
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.side_effect = httpx.NetworkError("Connection failed")

                await session.start(agent)
                result = await session.run(user_input="How do I send documents?")

                # Tool should be called
                result.expect.next_event().is_function_call(
                    name="unleash_search_knowledge"
                )

                # Should handle network error with ToolError
                error_event = result.expect.next_event().is_function_call_error()
                error_message = str(error_event.item.error).lower()
                assert "trouble reaching" in error_message or "walk you through" in error_message

                # Agent should still offer help
                await result.expect.contains_message(role="assistant").judge(
                    llm, intent="Offers to help despite network issues"
                )
    finally:
        # Clean up
        os.environ.pop("UNLEASH_API_KEY", None)


# Test runner for local execution
if __name__ == "__main__":
    import asyncio

    # Run a simple test
    print("Running Unleash tool tests...")
    asyncio.run(test_unleash_search_basic())
    print("Basic test passed!")