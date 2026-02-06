"""Configuration management for Apprentice MCP Agent."""

import json
import os
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI API Key
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

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

    # MCP config (loaded from mcp_config.json)
    mcp_config: Dict = Field(default_factory=dict)


# Global settings instance
_settings: Optional[Settings] = None


def _substitute_placeholders(config: Any, settings: Settings) -> Any:
    """Recursively substitute placeholders in the config."""
    if isinstance(config, dict):
        return {k: _substitute_placeholders(v, settings) for k, v in config.items()}
    if isinstance(config, list):
        return [_substitute_placeholders(i, settings) for i in config]
    if isinstance(config, str):
        # Regex to find ${VAR_NAME} placeholders
        placeholder_pattern = re.compile(r"\$\{(\w+)\}")
        
        def replace_match(match):
            var_name = match.group(1)
            # Use getattr on the settings object to get the value
            # The attribute names in Settings are lowercase
            return getattr(settings, var_name.lower(), f"${{{var_name}}}")

        return placeholder_pattern.sub(replace_match, config)
    return config


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
        # Load mcp_config.json
        config_path = Path("mcp_config.json")
        if config_path.exists():
            with open(config_path, "r") as f:
                raw_config = json.load(f)
                _settings.mcp_config = _substitute_placeholders(raw_config, _settings)
        else:
            print("Warning: mcp_config.json not found. MCP servers will not be configured.")
    return _settings
