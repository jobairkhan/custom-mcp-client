"""Tests for agent module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.tools import BaseTool

from src.agent import ApprenticeAgent
from src.mcp_client import MultiServerMCPClient


class TestApprenticeAgent:
    """Test suite for ApprenticeAgent."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        mock_client = MagicMock(spec=MultiServerMCPClient)
        mock_tools = []
        
        with patch("src.agent.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "test-key"
            mock_settings.return_value.max_iterations = 15
            mock_settings.return_value.github_org = "test-org"
            mock_settings.return_value.github_assignee = "test-user"
            
            agent = ApprenticeAgent(mock_client, mock_tools)
            
            assert agent.mcp_client is mock_client
            assert agent.tools == mock_tools
            assert agent.graph is not None
