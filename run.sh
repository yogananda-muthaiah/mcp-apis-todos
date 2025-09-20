# run_server.sh - Startup script
#!/bin/bash

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export PYTHONUNBUFFERED=1

# Create logs directory
mkdir -p logs

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install requirements if not installed
pip install -r requirements.txt

# Run the MCP server
echo "Starting MCP API Server..."
python mcp_server.py