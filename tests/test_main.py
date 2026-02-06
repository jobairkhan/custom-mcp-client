"""Tests for main CLI module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.main import format_output, main_async


class TestFormatOutput:
    """Test suite for output formatting."""

    def test_format_output_success_json(self):
        """Test JSON output formatting for successful execution."""
        result = {
            "success": True,
            "jira_key": "PROJ-123",
            "iterations": 5
        }
        
        output = format_output(result, json_output=True)
        parsed = json.loads(output)
        
        assert parsed["success"] is True
        assert parsed["jira_key"] == "PROJ-123"

    def test_format_output_success_human(self):
        """Test human-readable output for successful execution."""
        result = {
            "success": True,
            "jira_key": "PROJ-123",
            "iterations": 5,
            "messages": []
        }
        
        output = format_output(result, json_output=False)
        
        assert "PROJ-123" in output
        assert "Success: True" in output
        assert "Iterations: 5" in output

    def test_format_output_error_json(self):
        """Test JSON output formatting for errors."""
        result = {
            "success": False,
            "jira_key": "PROJ-123",
            "error": "Connection failed"
        }
        
        output = format_output(result, json_output=True)
        parsed = json.loads(output)
        
        assert parsed["success"] is False
        assert parsed["error"] == "Connection failed"

    def test_format_output_error_human(self):
        """Test human-readable output for errors."""
        result = {
            "success": False,
            "jira_key": "PROJ-123",
            "error": "Connection failed"
        }
        
        output = format_output(result, json_output=False)
        
        assert "PROJ-123" in output
        assert "Success: False" in output
        assert "Connection failed" in output


class TestMainAsync:
    """Test suite for main async function."""

    @pytest.mark.asyncio
    async def test_main_async_no_servers(self):
        """Test main async with no MCP servers configured."""
        with patch("src.main.get_settings") as mock_settings:
            mock_instance = MagicMock()
            mock_instance.mcp_servers = "[]"
            mock_instance.log_level = "INFO"
            mock_settings.return_value = mock_instance
            
            result = await main_async("PROJ-123")
            
            assert result["success"] is False
            assert "No MCP servers configured" in result["error"]

    @pytest.mark.asyncio
    async def test_main_async_invalid_json(self):
        """Test main async with invalid MCP servers JSON."""
        with patch("src.main.get_settings") as mock_settings:
            mock_instance = MagicMock()
            mock_instance.mcp_servers = "invalid json"
            mock_instance.log_level = "INFO"
            mock_settings.return_value = mock_instance
            
            result = await main_async("PROJ-123")
            
            assert result["success"] is False
