# Custom MCP Client

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

4. Configure your `.env` file with your secrets. See the "Configuration" section for more details.

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

The application is configured through a combination of `mcp_config.json` and a `.env` file.

- **`mcp_config.json`**: This file contains non-secret configuration and is checked into version control. It uses placeholders in the format `${VAR_NAME}` to refer to secrets that are loaded from the environment.
- **`.env`**: This file is used for storing secrets and local environment-specific variables. It is not checked into version control. You can create one by copying the `.env.example` file.

### Environment Variables

The following variables must be defined in your `.env` file:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key. |
| `GITHUB_TOKEN` | Yes | Your GitHub personal access token. |
| `GITHUB_ORG`| Yes | The GitHub organization to create issues in. |
| `GITHUB_ASSIGNEE`| No | The GitHub username to assign issues to. |
| `JIRA_URL` | Yes | The URL of your Jira instance. |
| `JIRA_USERNAME` | Yes | Your Jira username or email. |
| `JIRA_API_TOKEN` | Yes | Your Jira API token. |
| `MAX_ITERATIONS` | No | Max agent iterations (default: 15) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |


## Development

### Setup

For development, install all dependencies (including testing and linting tools) from `requirements-dev.txt`:

```bash
pip install -r requirements-dev.txt
```

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
├── mcp_config.json          # MCP server configuration
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Python development dependencies
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
