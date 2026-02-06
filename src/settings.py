"""Configuration management for Apprentice MCP Agent."""

from typing import Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI API Key
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

    # MCP Server configurations
    # Format: JSON string with server configs
    # Example: [{"name": "jira", "type": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-jira"]}]
    mcp_servers: str = Field(
        default='[]',
        alias="MCP_SERVERS",
        description="JSON string containing MCP server configurations"
    )

    # GitHub organization (placeholder support)
    github_org: Optional[str] = Field(None, alias="GITHUB_ORG")

    # Default assignee for GitHub issues (placeholder support)
    github_assignee: Optional[str] = Field(None, alias="GITHUB_ASSIGNEE")

    # Jira configuration (if needed for placeholders)
    jira_url: Optional[str] = Field(None, alias="JIRA_URL")
    jira_username: Optional[str] = Field(None, alias="JIRA_USERNAME")
    jira_api_token: Optional[str] = Field(None, alias="JIRA_API_TOKEN")

    # GitHub token (if needed for placeholders)
    github_token: Optional[str] = Field(None, alias="GITHUB_TOKEN")

    # LangGraph settings
    max_iterations: int = Field(default=15, alias="MAX_ITERATIONS")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
