# Apprentice MCP Agent

A LangGraph-based ReAct agent that automates Jira to GitHub issue migration using Model Context Protocol (MCP) servers.

## Features

- 🤖 **LangGraph ReAct Agent**: Intelligent reasoning and action with OpenAI GPT models
- 🔌 **Dynamic MCP Tool Loading**: Automatically loads tools from MCP servers (no manual wrappers needed)
- 🔄 **Multi-Server Support**: Connect to multiple MCP servers (Jira, GitHub, etc.) simultaneously
- 🚀 **Dual Interface**: CLI and AWS Lambda support
- ⚙️ **Flexible Configuration**: Environment-based config with `.env` file support
- 📊 **Multiple Output Formats**: Human-readable or JSON output

## Architecture

```
┌─────────────┐
│   CLI/Lambda │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ ApprenticeAgent │ (LangGraph ReAct)
└──────┬──────────┘
       │
       ▼
┌──────────────────────┐
│ MultiServerMCPClient │
└──────┬───────────────┘
       │
       ├─────────────┬─────────────┐
       ▼             ▼             ▼
   ┌──────┐     ┌──────┐      ┌──────┐
   │ Jira │     │GitHub│  ... │ Other│
   │ MCP  │     │ MCP  │      │ MCP  │
   └──────┘     └──────┘      └──────┘
```

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ (for MCP servers)
- OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/jobairkhan/custom-mcp-client.git
cd custom-mcp-client
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. Configure your `.env` file with required credentials:
```env
OPENAI_API_KEY=your-openai-api-key
GITHUB_TOKEN=your-github-token
JIRA_URL=https://your-instance.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
GITHUB_ORG=your-org
GITHUB_ASSIGNEE=your-username

# Configure MCP servers (JSON array)
MCP_SERVERS=[{"name":"jira","type":"stdio","command":"npx","args":["-y","@modelcontextprotocol/server-jira"]},{"name":"github","type":"stdio","command":"npx","args":["-y","@modelcontextprotocol/server-github"]}]
```

## Usage

### CLI Mode

Basic usage:
```bash
python -m src.main PROJ-123
```

With verbose logging:
```bash
python -m src.main PROJ-123 --verbose
```

JSON output:
```bash
python -m src.main PROJ-123 --json
```

### AWS Lambda

The Lambda handler expects an event with a `jira_key` parameter:

**Direct invocation:**
```json
{
  "jira_key": "PROJ-123"
}
```

**API Gateway:**
```json
{
  "body": "{\"jira_key\": \"PROJ-123\"}"
}
```

#### Deploying to AWS Lambda

1. Package the application:
```bash
pip install -r requirements.txt -t package/
cp -r src package/
cd package && zip -r ../deployment.zip . && cd ..
```

2. Create Lambda function with Python 3.10+ runtime
3. Set handler to `src.lambda_handler.lambda_handler`
4. Configure environment variables from `.env`
5. Increase timeout (recommended: 5 minutes)
6. Increase memory (recommended: 512 MB)

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT models |
| `MCP_SERVERS` | Yes | JSON array of MCP server configurations |
| `GITHUB_TOKEN` | No | GitHub personal access token |
| `GITHUB_ORG` | No | Default GitHub organization |
| `GITHUB_ASSIGNEE` | No | Default assignee for GitHub issues |
| `JIRA_URL` | No | Jira instance URL |
| `JIRA_USERNAME` | No | Jira username/email |
| `JIRA_API_TOKEN` | No | Jira API token |
| `MAX_ITERATIONS` | No | Max agent iterations (default: 15) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

### MCP Server Configuration

MCP servers are configured via the `MCP_SERVERS` environment variable as a JSON array:

```json
[
  {
    "name": "jira",
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-jira"],
    "env": {
      "JIRA_URL": "https://your-instance.atlassian.net",
      "JIRA_USERNAME": "your-email@example.com",
      "JIRA_API_TOKEN": "your-token"
    }
  },
  {
    "name": "github",
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_TOKEN": "your-token"
    }
  }
]
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

### Project Structure

```
custom-mcp-client/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── settings.py          # Configuration management
│   ├── mcp_client.py        # MCP client integration
│   ├── agent.py             # LangGraph ReAct agent
│   ├── main.py              # CLI entry point
│   └── lambda_handler.py    # AWS Lambda handler
├── tests/
│   ├── __init__.py
│   ├── test_settings.py
│   ├── test_mcp_client.py
│   ├── test_agent.py
│   └── test_main.py
├── .env.example             # Example environment configuration
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
└── README.md              # This file
```

## How It Works

1. **Initialization**: The agent loads configuration and connects to configured MCP servers
2. **Tool Discovery**: Tools are dynamically loaded from all connected MCP servers
3. **Agent Execution**: LangGraph ReAct agent processes the Jira key:
   - Fetches Jira issue details
   - Extracts relevant information
   - Creates a GitHub issue with the information
   - Links back to the Jira issue
4. **Result**: Returns execution status and details

## MCP (Model Context Protocol)

This project uses the Model Context Protocol to integrate with external services. MCP provides a standardized way for AI assistants to interact with tools and data sources.

Learn more: [MCP Documentation](https://modelcontextprotocol.io)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
