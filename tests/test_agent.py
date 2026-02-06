"""Tests for agent module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agent import ApprenticeAgent, MCPToolWrapper
from src.mcp_client import MultiServerMCPClient


class TestMCPToolWrapper:
    """Test suite for MCPToolWrapper."""

    @pytest.mark.asyncio
    async def test_tool_wrapper_initialization(self):
        """Test MCPToolWrapper initialization."""
        mock_client = MagicMock(spec=MultiServerMCPClient)
        
        wrapper = MCPToolWrapper(
            mcp_client=mock_client,
            tool_name="test.tool",
            tool_description="Test tool description",
            tool_schema={"type": "object"}
        )
        
        assert wrapper.name == "test_tool"  # Dots replaced with underscores
        assert wrapper.description == "Test tool description"
        assert wrapper.tool_name == "test.tool"

    @pytest.mark.asyncio
    async def test_tool_wrapper_sync_run_raises(self):
        """Test that sync run raises NotImplementedError."""
        mock_client = MagicMock(spec=MultiServerMCPClient)
        
        wrapper = MCPToolWrapper(
            mcp_client=mock_client,
            tool_name="test.tool",
            tool_description="Test tool",
            tool_schema={}
        )
        
        with pytest.raises(NotImplementedError):
            wrapper._run()

    @pytest.mark.asyncio
    async def test_tool_wrapper_async_run(self):
        """Test async tool execution."""
        mock_client = MagicMock(spec=MultiServerMCPClient)
        mock_result = MagicMock()
        mock_result.content = "Test result"
        mock_client.call_tool = AsyncMock(return_value=mock_result)
        
        wrapper = MCPToolWrapper(
            mcp_client=mock_client,
            tool_name="test.tool",
            tool_description="Test tool",
            tool_schema={}
        )
        
        result = await wrapper._arun(arg1="value1")
        
        assert result == "Test result"
        mock_client.call_tool.assert_called_once_with("test.tool", {"arg1": "value1"})


class TestApprenticeAgent:
    """Test suite for ApprenticeAgent."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        mock_client = MagicMock(spec=MultiServerMCPClient)
        mock_client.get_all_tools.return_value = {}
        
        with patch("src.agent.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "test-key"
            mock_settings.return_value.max_iterations = 15
            mock_settings.return_value.github_org = "test-org"
            mock_settings.return_value.github_assignee = "test-user"
            
            agent = ApprenticeAgent(mock_client)
            
            assert agent.mcp_client is mock_client
            assert agent.tools == []
            assert agent.graph is not None

    @pytest.mark.asyncio
    async def test_create_langchain_tools(self):
        """Test creating LangChain tools from MCP tools."""
        mock_client = MagicMock(spec=MultiServerMCPClient)
        mock_client.get_all_tools.return_value = {
            "jira.getIssue": {
                "description": "Get Jira issue",
                "inputSchema": {"type": "object"}
            },
            "github.createIssue": {
                "description": "Create GitHub issue",
                "inputSchema": {"type": "object"}
            }
        }
        
        with patch("src.agent.get_settings") as mock_settings:
            mock_settings.return_value.openai_api_key = "test-key"
            mock_settings.return_value.max_iterations = 15
            
            agent = ApprenticeAgent(mock_client)
            
            assert len(agent.tools) == 2
            assert agent.tools[0].name == "jira_getIssue"
            assert agent.tools[1].name == "github_createIssue"
