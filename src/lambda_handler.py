"""
AWS Lambda handler for Apprentice MCP Agent.

Expects an event with a 'jira_key' parameter.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict

from src.settings import get_settings
from src.mcp_client import MultiServerMCPClient, parse_mcp_servers_config
from src.agent import ApprenticeAgent

# Configure logging for Lambda
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def process_jira_issue(jira_key: str) -> Dict[str, Any]:
    """
    Process a Jira issue asynchronously.
    
    Args:
        jira_key: The Jira issue key to process
        
    Returns:
        Dictionary with execution results
    """
    try:
        # Load settings
        settings = get_settings()
        logger.info(f"Processing Jira issue: {jira_key}")
        
        # Parse MCP server configurations
        server_configs = parse_mcp_servers_config(settings.mcp_servers)
        if not server_configs:
            raise ValueError("No MCP servers configured")
        
        # Initialize MCP client
        mcp_client = MultiServerMCPClient(server_configs)
        
        try:
            # Connect to MCP servers
            await mcp_client.connect_all()
            
            # Check if we have tools
            tools = mcp_client.get_all_tools()
            if not tools:
                raise ValueError("No tools loaded from MCP servers")
            
            logger.info(f"Loaded {len(tools)} tool(s) from MCP servers")
            
            # Initialize agent
            agent = ApprenticeAgent(mcp_client)
            
            # Run the agent
            result = await agent.run(jira_key)
            
            return result
            
        finally:
            # Cleanup MCP client
            await mcp_client.cleanup()
            
    except Exception as e:
        logger.error(f"Error processing Jira issue: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "jira_key": jira_key
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.
    
    Expected event format:
    {
        "jira_key": "PROJ-123"
    }
    
    Or API Gateway format:
    {
        "body": "{\"jira_key\": \"PROJ-123\"}"
    }
    
    Args:
        event: Lambda event dictionary
        context: Lambda context object
        
    Returns:
        Response dictionary with statusCode and body
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract jira_key from event
        jira_key = None
        
        # Direct invocation
        if "jira_key" in event:
            jira_key = event["jira_key"]
        # API Gateway invocation
        elif "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
            jira_key = body.get("jira_key")
        
        if not jira_key:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "success": False,
                    "error": "Missing required parameter: jira_key"
                })
            }
        
        # Run the async process
        result = asyncio.run(process_jira_issue(jira_key))
        
        # Format response
        status_code = 200 if result.get("success", False) else 500
        
        # Convert messages to strings for JSON serialization
        if "messages" in result:
            result["messages"] = [str(msg) for msg in result["messages"]]
        
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(result, default=str)
        }
        
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }
