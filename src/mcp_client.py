"""MCP Client integration for connecting to multiple MCP servers."""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MultiServerMCPClient:
    """
    Client for managing connections to multiple MCP servers.
    
    Supports both stdio and HTTP transport protocols.
    Dynamically loads tools from all connected servers.
    """

    def __init__(self, server_configs: List[Dict[str, Any]]):
        """
        Initialize the multi-server MCP client.
        
        Args:
            server_configs: List of server configuration dictionaries
                Each config should have:
                - name: Server identifier
                - type: "stdio" or "http"
                - For stdio: command, args, env (optional)
                - For http: url, headers (optional)
        """
        self.server_configs = server_configs
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: Dict[str, Any] = {}
        self._clients: List[Any] = []

    async def connect_all(self) -> None:
        """Connect to all configured MCP servers."""
        for config in self.server_configs:
            try:
                await self._connect_server(config)
            except Exception as e:
                logger.error(f"Failed to connect to server {config.get('name', 'unknown')}: {e}")
                # Continue with other servers even if one fails

    async def _connect_server(self, config: Dict[str, Any]) -> None:
        """
        Connect to a single MCP server.
        
        Args:
            config: Server configuration dictionary
        """
        server_name = config.get("name", "unknown")
        server_type = config.get("type", "stdio")

        logger.info(f"Connecting to MCP server: {server_name} ({server_type})")

        if server_type == "stdio":
            await self._connect_stdio_server(server_name, config)
        elif server_type == "http":
            await self._connect_http_server(server_name, config)
        else:
            raise ValueError(f"Unsupported server type: {server_type}")

    async def _connect_stdio_server(self, name: str, config: Dict[str, Any]) -> None:
        """Connect to an stdio-based MCP server."""
        command = config.get("command")
        args = config.get("args", [])
        env = config.get("env")

        if not command:
            raise ValueError(f"Missing 'command' for stdio server {name}")

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )

        # Create stdio client context
        stdio = stdio_client(server_params)
        read, write = await stdio.__aenter__()
        self._clients.append(stdio)

        # Create session
        session = ClientSession(read, write)
        await session.__aenter__()
        self.sessions[name] = session

        # Initialize the session
        await session.initialize()

        # Load tools from this server
        await self._load_tools_from_session(name, session)

    async def _connect_http_server(self, name: str, config: Dict[str, Any]) -> None:
        """Connect to an HTTP-based MCP server."""
        # HTTP client support - to be implemented
        # For now, raise not implemented
        raise NotImplementedError("HTTP MCP servers not yet implemented")

    async def _load_tools_from_session(self, server_name: str, session: ClientSession) -> None:
        """
        Load all tools from a connected session.
        
        Args:
            server_name: Name of the server
            session: Active MCP client session
        """
        try:
            # List available tools
            tools_result = await session.list_tools()
            
            # Store tools with server prefix
            for tool in tools_result.tools:
                tool_key = f"{server_name}.{tool.name}"
                self.tools[tool_key] = {
                    "server": server_name,
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                    "session": session
                }
                logger.info(f"Loaded tool: {tool_key}")
                
        except Exception as e:
            logger.error(f"Failed to load tools from {server_name}: {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the appropriate MCP server.
        
        Args:
            tool_name: Full tool name (server.tool_name)
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")

        tool_info = self.tools[tool_name]
        session = tool_info["session"]
        actual_tool_name = tool_info["name"]

        logger.info(f"Calling tool {tool_name} with args: {arguments}")

        try:
            result = await session.call_tool(actual_tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise

    def get_all_tools(self) -> Dict[str, Any]:
        """
        Get all available tools from all servers.
        
        Returns:
            Dictionary of all loaded tools
        """
        return self.tools

    async def cleanup(self) -> None:
        """Close all MCP server connections."""
        for name, session in self.sessions.items():
            try:
                await session.__aexit__(None, None, None)
                logger.info(f"Closed session: {name}")
            except Exception as e:
                logger.error(f"Error closing session {name}: {e}")

        for client in self._clients:
            try:
                await client.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing client: {e}")

        self.sessions.clear()
        self.tools.clear()
        self._clients.clear()


def parse_mcp_servers_config(config_string: str) -> List[Dict[str, Any]]:
    """
    Parse MCP servers configuration from JSON string.
    
    Args:
        config_string: JSON string containing server configurations
        
    Returns:
        List of server configuration dictionaries
    """
    try:
        return json.loads(config_string)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse MCP servers config: {e}")
        return []
