"""MCP Client integration using langchain-mcp-adapters."""

import logging
from typing import Any, Dict, List

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient as LangChainMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

logger = logging.getLogger(__name__)


class MultiServerMCPClient:
    """Wrapper around langchain-mcp-adapters client with persistent sessions."""

    def __init__(self, connections: Dict[str, Any]):
        """Initialize MCP client with server connections.
        
        Args:
            connections: Dict mapping server names to connection configs.
                        Format: {"server_name": {"command": ..., "args": [...], 
                                "transport": "stdio", "env": {...}}}
        """
        self.connections = connections
        self.client = LangChainMCPClient(
            connections=connections,
            tool_name_prefix=True  # Prefix tools with server name to avoid conflicts
        )
        self._all_tools: List[BaseTool] = []
        logger.info(f"Initialized MCP client with {len(connections)} server(s)")

    async def load_tools(self) -> List[BaseTool]:
        """Load all tools from all servers using persistent sessions.
        
        Uses persistent sessions for better performance.
        
        Returns:
            List of LangChain BaseTool instances
        """
        all_tools: List[BaseTool] = []
        
        for server_name in self.connections.keys():
            try:
                logger.info(f"Loading tools from {server_name}")
                # Use persistent session for each server
                async with self.client.session(server_name) as session:
                    tools = await load_mcp_tools(
                        session,
                        server_name=server_name,
                        tool_name_prefix=True
                    )
                    all_tools.extend(tools)
                    logger.info(f"Loaded {len(tools)} tool(s) from {server_name}")
            except Exception as e:
                logger.error(f"Failed to load tools from {server_name}: {e}")
                # Continue with other servers even if one fails
        
        self._all_tools = all_tools
        logger.info(f"Total tools loaded: {len(all_tools)}")
        return all_tools

    def get_all_tools(self) -> List[BaseTool]:
        """Get all loaded tools.
        
        Returns:
            List of LangChain BaseTool instances
        """
        return self._all_tools

    async def cleanup(self) -> None:
        """Cleanup resources (no-op for langchain-mcp-adapters).
        
        langchain-mcp-adapters manages sessions automatically,
        but keep this method for API compatibility.
        """
        logger.info("Cleanup called (managed by langchain-mcp-adapters)")
        self._all_tools.clear()
