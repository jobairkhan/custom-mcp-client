"""Tests for MCP client module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.tools import BaseTool

from src.mcp_client import MultiServerMCPClient


class TestMCPClient:
    """Test suite for MultiServerMCPClient."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test MCP client initialization."""
        connections = {
            "test": {
                "command": "echo",
                "args": [],
                "transport": "stdio"
            }
        }
        client = MultiServerMCPClient(connections)
        
        assert client.connections == connections
        assert len(client._all_tools) == 0

    @pytest.mark.asyncio
    async def test_get_all_tools_empty(self):
        """Test getting tools when none are loaded."""
        client = MultiServerMCPClient({})
        tools = client.get_all_tools()
        
        assert tools == []

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup."""
        client = MultiServerMCPClient({})
        
        # Should not raise any errors
        await client.cleanup()
        
        assert len(client._all_tools) == 0
