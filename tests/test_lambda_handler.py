"""Tests for Lambda handler module."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.lambda_handler import lambda_handler, execute_agent


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
        assert "Missing jira_key" in body["error"]

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
