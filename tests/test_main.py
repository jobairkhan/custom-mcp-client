"""Tests for main CLI module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.main import format_output


class TestFormatOutput:
    """Test suite for output formatting."""

    def test_format_output_success_json(self):
        """Test JSON output formatting for successful execution."""
        result = {
            "success": True,
            "jira_key": "PROJ-123",
            "iterations": 5
        }
        
        output = format_output(result, as_json=True)
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
        
        output = format_output(result, as_json=False)
        
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
        
        output = format_output(result, as_json=True)
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
        
        output = format_output(result, as_json=False)
        
        assert "PROJ-123" in output
        assert "Success: False" in output
        assert "Connection failed" in output
