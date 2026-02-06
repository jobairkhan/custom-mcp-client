"""Tests for MCP client module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.mcp_client import MultiServerMCPClient, parse_mcp_servers_config


class TestMCPClient:
    """Test suite for MultiServerMCPClient."""

    def test_parse_mcp_servers_config_valid(self):
        """Test parsing valid MCP server configuration."""
        config_str = '[{"name":"jira","type":"stdio","command":"npx"}]'
        result = parse_mcp_servers_config(config_str)
        
        assert len(result) == 1
        assert result[0]["name"] == "jira"
        assert result[0]["type"] == "stdio"

    def test_parse_mcp_servers_config_invalid(self):
        """Test parsing invalid MCP server configuration."""
        config_str = "invalid json"
        result = parse_mcp_servers_config(config_str)
        
        assert result == []

    def test_parse_mcp_servers_config_empty(self):
        """Test parsing empty configuration."""
        config_str = "[]"
        result = parse_mcp_servers_config(config_str)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test MCP client initialization."""
        configs = [{"name": "test", "type": "stdio", "command": "echo"}]
        client = MultiServerMCPClient(configs)
        
        assert client.server_configs == configs
        assert len(client.sessions) == 0
        assert len(client.tools) == 0

    @pytest.mark.asyncio
    async def test_get_all_tools_empty(self):
        """Test getting tools when none are loaded."""
        client = MultiServerMCPClient([])
        tools = client.get_all_tools()
        
        assert tools == {}

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self):
        """Test calling a tool that doesn't exist."""
        client = MultiServerMCPClient([])
        
        with pytest.raises(ValueError, match="Tool not found"):
            await client.call_tool("nonexistent.tool", {})


class TestMultiServerMCPClient:
    """Integration tests for MultiServerMCPClient."""

    @pytest.mark.asyncio
    async def test_cleanup_empty_client(self):
        """Test cleanup on a client with no connections."""
        client = MultiServerMCPClient([])
        
        # Should not raise any errors
        await client.cleanup()
        
        assert len(client.sessions) == 0
        assert len(client.tools) == 0
