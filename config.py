# config.py - Configuration file for your APIs
"""
Configuration file for MCP Server APIs
Add your API configurations here
"""

from typing import Dict, Any

# Your API configurations
API_CONFIGS = [
    {
        "name": "your_api_1",
        "base_url": "https://api.example1.com/v1",
        "endpoints": {
            "get_users": {
                "path": "/users",
                "method": "GET",
                "description": "Get all users"
            },
            "create_user": {
                "path": "/users",
                "method": "POST",
                "description": "Create a new user"
            },
            "get_user_by_id": {
                "path": "/users/{user_id}",
                "method": "GET",
                "description": "Get user by ID"
            }
        },
        "headers": {
            "Content-Type": "application/json",
            "X-API-Key": "your_api_key_here"
        }
    },
    {
        "name": "your_api_2", 
        "base_url": "https://api.example2.com",
        "endpoints": {
            "get_products": {
                "path": "/products",
                "method": "GET",
                "description": "Get all products"
            },
            "search_products": {
                "path": "/products/search",
                "method": "GET",
                "description": "Search products"
            }
        },
        "auth_token": "bearer_token_here"
    }
]

# requirements.txt content
REQUIREMENTS = """
mcp>=1.0.0
httpx>=0.25.0
pydantic>=2.0.0
asyncio
"""

# client_example.py - How to interact with your MCP server
CLIENT_EXAMPLE = '''
"""
Example client to test the MCP server
Run this after starting your MCP server
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
            
            # Example: Call an API endpoint
            result = await session.call_tool(
                "call_api",
                {
                    "api_name": "jsonplaceholder",
                    "endpoint_name": "get_posts",
                    "params": {"_limit": 5}
                }
            )
            
            print("\\nAPI Result:")
            print(result.content[0].text)
            
            # Example: Get weather data (if configured)
            weather_result = await session.call_tool(
                "weather_api_current_weather",
                {
                    "params": {
                        "q": "London",
                        "appid": "your_weather_api_key"
                    }
                }
            )
            
            print("\\nWeather Result:")
            print(weather_result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
'''

print("=== Configuration Example ===")
print("Create a config.py file with your API configurations:")
print(json.dumps(API_CONFIGS, indent=2))

print("\n=== Requirements ===")
print("Create requirements.txt:")
print(REQUIREMENTS)

print("\n=== Client Example ===")
print("Create client_example.py to test your server:")
print(CLIENT_EXAMPLE)