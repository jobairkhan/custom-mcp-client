#!/bin/bash
# Development setup script

set -e

echo "Setting up Apprentice MCP Agent development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements-dev.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your credentials"
fi

echo ""
echo "Setup complete! To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "Don't forget to configure your .env file with:"
echo "  - OPENAI_API_KEY"
echo "  - GITHUB_TOKEN"
echo "  - JIRA credentials"
echo "  - MCP_SERVERS configuration"
