"""Configuration management for Apprentice MCP Agent."""

import json
import os
from typing import Dict, Optional, Any
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and mcp_config.json."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    github_org: Optional[str] = Field(None, alias="GITHUB_ORG")
    github_assignee: Optional[str] = Field(None, alias="GITHUB_ASSIGNEE")
    jira_url: Optional[str] = Field(None, alias="JIRA_URL")
    jira_username: Optional[str] = Field(None, alias="JIRA_USERNAME")
    jira_api_token: Optional[str] = Field(None, alias="JIRA_API_TOKEN")
    github_token: Optional[str] = Field(None, alias="GITHUB_TOKEN")
    max_iterations: int = Field(default=15, alias="MAX_ITERATIONS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    mcp_config: Dict = Field(default_factory=dict)


_settings: Optional[Settings] = None


def _substitute_placeholders(obj: Any, env: Dict[str, str]) -> Any:
    """Recursively replace ${VAR} placeholders with environment values."""
    if isinstance(obj, dict):
        return {k: _substitute_placeholders(v, env) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute_placeholders(i, env) for i in obj]
    if isinstance(obj, str):
        for var, value in env.items():
            obj = obj.replace(f"${{{var}}}", str(value))
        return obj
    return obj


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
        config_path = Path("mcp_config.json")
        if config_path.exists():
            with open(config_path) as f:
                raw_config = json.load(f)
                # Substitute placeholders with environment variables
                env_dict = {k: str(getattr(_settings, k.lower(), os.environ.get(k, ""))) 
                           for k in os.environ.keys()}
                # Config is already in the correct format for langchain-mcp-adapters
                _settings.mcp_config = _substitute_placeholders(raw_config, env_dict)
    return _settings
