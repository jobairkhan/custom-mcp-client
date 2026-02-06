"""Tests for settings module."""

import os
import pytest
from unittest.mock import patch

from src.settings import Settings, get_settings


class TestSettings:
    """Test suite for Settings class."""

    def test_settings_from_env(self, monkeypatch):
        """Test settings load from environment variables."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        monkeypatch.setenv("MCP_SERVERS", '[{"name":"test","type":"stdio"}]')
        monkeypatch.setenv("GITHUB_ORG", "test-org")
        monkeypatch.setenv("MAX_ITERATIONS", "20")
        
        settings = Settings()
        
        assert settings.openai_api_key == "test-key-123"
        assert settings.mcp_servers == '[{"name":"test","type":"stdio"}]'
        assert settings.github_org == "test-org"
        assert settings.max_iterations == 20

    def test_settings_defaults(self, monkeypatch):
        """Test default values for optional settings."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        settings = Settings()
        
        assert settings.max_iterations == 15
        assert settings.log_level == "INFO"
        assert settings.mcp_servers == "[]"

    def test_get_settings_singleton(self, monkeypatch):
        """Test that get_settings returns a singleton."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        # Reset the global settings
        import src.settings
        src.settings._settings = None
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_settings_optional_fields(self, monkeypatch):
        """Test optional configuration fields."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GITHUB_TOKEN", "github-token")
        monkeypatch.setenv("JIRA_URL", "https://test.atlassian.net")
        
        settings = Settings()
        
        assert settings.github_token == "github-token"
        assert settings.jira_url == "https://test.atlassian.net"
