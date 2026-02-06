"""CLI entry point for Apprentice MCP Agent."""

import argparse
import asyncio
import json
import logging
import sys
from typing import Any, Dict

from src.lambda_handler import execute_agent


def format_output(result: Dict[str, Any], as_json: bool = False) -> str:
    """Format result for display."""
    if as_json:
        return json.dumps(result, indent=2, default=str)
    
    lines = [
        "=" * 60,
        "Apprentice MCP Agent - Result",
        "=" * 60,
        f"Jira Key: {result.get('jira_key', 'N/A')}",
        f"Success: {result.get('success', False)}"
    ]
    
    if result.get("success"):
        lines.append(f"Iterations: {result.get('iterations', 0)}")
        messages = result.get("messages", [])
        if messages:
            lines.append("\nAgent Output:")
            lines.append("-" * 60)
            for i, msg in enumerate(messages, 1):
                msg_type = type(msg).__name__
                content = getattr(msg, 'content', str(msg))
                lines.append(f"{i}. [{msg_type}] {content}")
    else:
        lines.append(f"Error: {result.get('error', 'Unknown')}")
    
    lines.append("=" * 60)
    return "\n".join(lines)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Apprentice MCP Agent - Jira to GitHub migration")
    parser.add_argument("jira_key", help="Jira issue key (e.g., PROJ-123)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s - %(message)s', stream=sys.stdout)
    
    # Run via lambda_handler's execute_agent
    result = asyncio.run(execute_agent(args.jira_key, args.verbose))
    print(format_output(result, args.json))
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()

