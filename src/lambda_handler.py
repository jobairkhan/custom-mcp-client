"""AWS Lambda handler for Apprentice MCP Agent."""

import asyncio
import json
import logging
from typing import Any, Dict

from src.agent import ApprenticeAgent
from src.mcp_client import MultiServerMCPClient
from src.settings import get_settings

logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def execute_agent(jira_key: str, verbose: bool = False) -> Dict[str, Any]:
    """Execute agent to migrate Jira issue. Core execution logic."""
    logger = logging.getLogger(__name__)
    try:
        settings = get_settings()
        if not settings.mcp_config:
            raise ValueError("No MCP servers configured")
        
        # Config is now a dict, not a list with "servers" key
        connections = settings.mcp_config
        if not connections:
            raise ValueError("No servers in mcp_config")
        
        mcp_client = MultiServerMCPClient(connections)
        try:
            # Load all tools using persistent sessions
            tools = await mcp_client.load_tools()
            if not tools:
                raise ValueError("No tools loaded from servers")
            
            agent = ApprenticeAgent(mcp_client, tools)
            return await agent.run(jira_key)
        finally:
            await mcp_client.cleanup()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=verbose)
        return {"success": False, "error": str(e), "jira_key": jira_key}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler supporting direct and API Gateway invocations."""
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        # Extract jira_key from event or body
        jira_key = event.get("jira_key")
        
        if not jira_key and "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
            jira_key = body.get("jira_key")
        
        if not jira_key:
            return {
                "statusCode": 400,
                "body": json.dumps({"success": False, "error": "Missing jira_key"})
            }
        
        # Run agent
        result = asyncio.run(execute_agent(jira_key, verbose=False))
        
        # Convert messages to strings for JSON
        if "messages" in result:
            result["messages"] = [str(msg) for msg in result["messages"]]
        
        status = 200 if result.get("success") else 500
        
        return {
            "statusCode": status,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result, default=str)
        }
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"success": False, "error": str(e)})
        }
