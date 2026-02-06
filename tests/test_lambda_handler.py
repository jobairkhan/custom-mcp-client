"""Tests for Lambda handler module."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.lambda_handler import lambda_handler, process_jira_issue


class TestLambdaHandler:
    """Test suite for AWS Lambda handler."""

    def test_lambda_handler_direct_invocation(self):
        """Test Lambda handler with direct invocation format."""
        event = {"jira_key": "PROJ-123"}
        context = MagicMock()
        
        with patch("src.lambda_handler.asyncio.run") as mock_run:
            mock_run.return_value = {
                "success": True,
                "jira_key": "PROJ-123"
            }
            
            response = lambda_handler(event, context)
            
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["success"] is True

    def test_lambda_handler_api_gateway_invocation(self):
        """Test Lambda handler with API Gateway format."""
        event = {
            "body": json.dumps({"jira_key": "PROJ-123"})
        }
        context = MagicMock()
        
        with patch("src.lambda_handler.asyncio.run") as mock_run:
            mock_run.return_value = {
                "success": True,
                "jira_key": "PROJ-123"
            }
            
            response = lambda_handler(event, context)
            
            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            assert body["success"] is True

    def test_lambda_handler_missing_jira_key(self):
        """Test Lambda handler with missing jira_key."""
        event = {}
        context = MagicMock()
        
        response = lambda_handler(event, context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False
        assert "Missing required parameter" in body["error"]

    def test_lambda_handler_error(self):
        """Test Lambda handler with processing error."""
        event = {"jira_key": "PROJ-123"}
        context = MagicMock()
        
        with patch("src.lambda_handler.asyncio.run") as mock_run:
            mock_run.return_value = {
                "success": False,
                "error": "Processing failed"
            }
            
            response = lambda_handler(event, context)
            
            assert response["statusCode"] == 500
            body = json.loads(response["body"])
            assert body["success"] is False

    def test_lambda_handler_exception(self):
        """Test Lambda handler with exception."""
        event = {"jira_key": "PROJ-123"}
        context = MagicMock()
        
        with patch("src.lambda_handler.asyncio.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")
            
            response = lambda_handler(event, context)
            
            assert response["statusCode"] == 500
            body = json.loads(response["body"])
            assert body["success"] is False


class TestProcessJiraIssue:
    """Test suite for process_jira_issue function."""

    @pytest.mark.asyncio
    async def test_process_jira_issue_no_servers(self):
        """Test processing with no MCP servers configured."""
        with patch("src.lambda_handler.get_settings") as mock_settings:
            mock_settings.return_value.mcp_servers = "[]"
            
            result = await process_jira_issue("PROJ-123")
            
            assert result["success"] is False
            assert "No MCP servers configured" in result["error"]

    @pytest.mark.asyncio
    async def test_process_jira_issue_exception(self):
        """Test processing with exception."""
        with patch("src.lambda_handler.get_settings") as mock_settings:
            mock_settings.return_value.mcp_servers = '[{"name":"test"}]'
            
            with patch("src.lambda_handler.MultiServerMCPClient") as mock_client_class:
                mock_client_class.side_effect = Exception("Connection error")
                
                result = await process_jira_issue("PROJ-123")
                
                assert result["success"] is False
                assert "Connection error" in result["error"]
