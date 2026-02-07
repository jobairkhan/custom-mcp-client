# Apprentice MCP Agent - Quick Start Guide

## What is this?

The Apprentice MCP Agent is an intelligent automation tool that uses AI (via OpenAI GPT models) and the Model Context Protocol (MCP) to automate the migration of issues from Jira to GitHub. It uses LangGraph's ReAct pattern to reason about actions and execute them intelligently.

## Quick Setup (5 minutes)

### 1. Prerequisites
- Python 3.13 or higher
- Node.js 18+ (for MCP servers)
- OpenAI API key
- GitHub personal access token
- Jira API credentials

### 2. Install

```bash
# Clone the repository
git clone https://github.com/jobairkhan/custom-mcp-client.git
cd custom-mcp-client

# Run the setup script
bash setup.sh

# Activate the virtual environment
source venv/bin/activate
```

### 3. Configure

Copy and edit the `.env` file:

```bash
cp .env.example .env
nano .env  # or use your favorite editor
```

**Minimal required configuration:**

```env
OPENAI_API_KEY=sk-your-api-key-here
GITHUB_TOKEN=ghp_your-github-token
GITHUB_ORG=your-organization
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# MCP Servers (copy this exactly)
MCP_SERVERS=[{"name":"jira","type":"stdio","command":"npx","args":["-y","@modelcontextprotocol/server-jira"]},{"name":"github","type":"stdio","command":"npx","args":["-y","@modelcontextprotocol/server-github"]}]
```

### 4. Run

```bash
# Basic usage
python -m src.main PROJ-123

# With verbose logging
python -m src.main PROJ-123 --verbose

# JSON output for scripting
python -m src.main PROJ-123 --json
```

## How It Works

1. **You provide a Jira issue key** (e.g., `PROJ-123`)
2. **The agent connects** to Jira and GitHub via MCP servers
3. **The AI reasons** about what actions to take using LangGraph's ReAct pattern
4. **Tools are called** to:
   - Fetch the Jira issue details
   - Extract relevant information
   - Create a GitHub issue
   - Link back to the original Jira issue
5. **Results are returned** with success/failure status

## Architecture Overview

```
User Command (CLI/Lambda)
        ↓
    Settings (.env)
        ↓
  ApprenticeAgent (LangGraph ReAct)
        ↓
  MultiServerMCPClient
        ↓
    ┌───┴───┐
    ↓       ↓
  Jira    GitHub
  MCP     MCP
```

## Key Features

✅ **Dynamic Tool Loading** - No manual tool wrappers needed  
✅ **Multi-Server Support** - Connect to multiple MCP servers simultaneously  
✅ **Intelligent Reasoning** - LangGraph ReAct pattern for smart decision-making  
✅ **Dual Interface** - CLI for local use, Lambda for cloud deployment  
✅ **Type-Safe Config** - Pydantic-based settings management  
✅ **Comprehensive Tests** - 29 passing tests with pytest  

## Common Use Cases

### Migrate a Single Issue
```bash
python -m src.main PROJ-123
```

### Batch Migration (shell script)
```bash
#!/bin/bash
for issue in PROJ-123 PROJ-124 PROJ-125; do
    python -m src.main $issue --json >> migration_log.json
done
```

### AWS Lambda Integration

Deploy as a Lambda function to create an API endpoint for issue migration:

```python
# Lambda invocation
{
  "jira_key": "PROJ-123"
}
```

## Troubleshooting

### "No MCP servers configured"
- Check that `MCP_SERVERS` is set in your `.env` file
- Ensure the JSON is valid (use a JSON validator)

### "No tools loaded from MCP servers"
- Make sure Node.js is installed and accessible
- Test MCP servers manually: `npx -y @modelcontextprotocol/server-jira`

### "OpenAI API error"
- Verify your `OPENAI_API_KEY` is valid
- Check your API quota and billing

### Connection errors
- Verify your Jira/GitHub credentials
- Check network connectivity
- Ensure API tokens have the correct permissions

## Advanced Configuration

### Custom MCP Servers

Add your own MCP servers to the `MCP_SERVERS` array:

```json
{
  "name": "custom-server",
  "type": "stdio",
  "command": "node",
  "args": ["/path/to/your/server.js"],
  "env": {
    "API_KEY": "your-key"
  }
}
```

### Adjust Agent Behavior

In `.env`:

```env
MAX_ITERATIONS=20  # Increase for complex migrations
LOG_LEVEL=DEBUG    # More detailed logging
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_agent.py -v
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Support

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/jobairkhan/custom-mcp-client/issues)
- 💬 [Discussions](https://github.com/jobairkhan/custom-mcp-client/discussions)

## License

MIT License - see [LICENSE](LICENSE) file for details.
