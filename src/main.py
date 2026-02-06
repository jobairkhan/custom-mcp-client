"""
Main CLI entry point for Apprentice MCP Agent.

Usage:
    python -m src.main <JIRA_KEY> [--verbose|--json]
"""

import argparse
import asyncio
import json
import logging
import sys
from typing import Any, Dict

from src.settings import get_settings
from src.mcp_client import MultiServerMCPClient, parse_mcp_servers_config
from src.agent import ApprenticeAgent


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    settings = get_settings()
    log_level = logging.DEBUG if verbose else getattr(logging, settings.log_level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


async def main_async(jira_key: str, verbose: bool = False, json_output: bool = False) -> Dict[str, Any]:
    """
    Async main function to run the agent.
    
    Args:
        jira_key: The Jira issue key to migrate
        verbose: Enable verbose logging
        json_output: Output results as JSON
        
    Returns:
        Dictionary with execution results
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Load settings
        settings = get_settings()
        logger.info("Settings loaded successfully")
        
        # Parse MCP server configurations
        server_configs = parse_mcp_servers_config(settings.mcp_servers)
        if not server_configs:
            raise ValueError("No MCP servers configured. Please check MCP_SERVERS in your .env file.")
        
        logger.info(f"Found {len(server_configs)} MCP server(s) configured")
        
        # Initialize MCP client
        mcp_client = MultiServerMCPClient(server_configs)
        
        try:
            # Connect to MCP servers
            logger.info("Connecting to MCP servers...")
            await mcp_client.connect_all()
            
            # Check if we have tools
            tools = mcp_client.get_all_tools()
            if not tools:
                raise ValueError("No tools loaded from MCP servers. Please check your MCP server configuration.")
            
            logger.info(f"Loaded {len(tools)} tool(s) from MCP servers")
            
            # Initialize agent
            logger.info("Initializing Apprentice agent...")
            agent = ApprenticeAgent(mcp_client)
            
            # Run the agent
            logger.info(f"Processing Jira issue: {jira_key}")
            result = await agent.run(jira_key)
            
            return result
            
        finally:
            # Cleanup MCP client
            await mcp_client.cleanup()
            logger.info("MCP client cleaned up")
            
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=verbose)
        return {
            "success": False,
            "error": str(e),
            "jira_key": jira_key
        }


def format_output(result: Dict[str, Any], json_output: bool = False) -> str:
    """
    Format the execution result for display.
    
    Args:
        result: Execution result dictionary
        json_output: Whether to output as JSON
        
    Returns:
        Formatted output string
    """
    if json_output:
        return json.dumps(result, indent=2, default=str)
    
    # Human-readable format
    output_lines = []
    output_lines.append("=" * 60)
    output_lines.append("Apprentice MCP Agent - Execution Result")
    output_lines.append("=" * 60)
    output_lines.append(f"Jira Key: {result.get('jira_key', 'N/A')}")
    output_lines.append(f"Success: {result.get('success', False)}")
    
    if result.get("success"):
        output_lines.append(f"Iterations: {result.get('iterations', 0)}")
        
        # Show messages
        messages = result.get("messages", [])
        if messages:
            output_lines.append("\nAgent Conversation:")
            output_lines.append("-" * 60)
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                content = getattr(msg, 'content', str(msg))
                output_lines.append(f"{i+1}. [{msg_type}] {content}")
    else:
        output_lines.append(f"Error: {result.get('error', 'Unknown error')}")
    
    output_lines.append("=" * 60)
    return "\n".join(output_lines)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Apprentice MCP Agent - Jira to GitHub migration tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main PROJ-123
  python -m src.main PROJ-123 --verbose
  python -m src.main PROJ-123 --json
        """
    )
    
    parser.add_argument(
        "jira_key",
        help="Jira issue key to migrate (e.g., PROJ-123)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Run async main
    result = asyncio.run(main_async(
        jira_key=args.jira_key,
        verbose=args.verbose,
        json_output=args.json
    ))
    
    # Output results
    output = format_output(result, json_output=args.json)
    print(output)
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success", False) else 1)


if __name__ == "__main__":
    main()
