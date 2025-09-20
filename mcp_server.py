#!/usr/bin/env python3
"""
MCP Server with API Integration
A Model Context Protocol server that interfaces with various APIs
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urljoin
import httpx
from pydantic import BaseModel, Field

# MCP SDK imports
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIEndpoint(BaseModel):
    """Configuration for an API endpoint"""
    name: str
    base_url: str
    endpoints: Dict[str, Dict[str, Any]]
    headers: Optional[Dict[str, str]] = None
    auth_token: Optional[str] = None

class APIManager:
    """Manages API calls to different endpoints"""
    
    def __init__(self):
        self.apis: Dict[str, APIEndpoint] = {}
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def register_api(self, api_config: APIEndpoint):
        """Register a new API configuration"""
        self.apis[api_config.name] = api_config
        logger.info(f"Registered API: {api_config.name}")
    
    async def call_api(self, api_name: str, endpoint_name: str, **kwargs) -> Dict[str, Any]:
        """Make an API call to a specific endpoint"""
        if api_name not in self.apis:
            raise ValueError(f"API '{api_name}' not found")
        
        api = self.apis[api_name]
        if endpoint_name not in api.endpoints:
            raise ValueError(f"Endpoint '{endpoint_name}' not found in API '{api_name}'")
        
        endpoint_config = api.endpoints[endpoint_name]
        
        # Build URL
        url = urljoin(api.base_url, endpoint_config.get("path", ""))
        
        # Prepare headers
        headers = {}
        if api.headers:
            headers.update(api.headers)
        if api.auth_token:
            headers["Authorization"] = f"Bearer {api.auth_token}"
        if endpoint_config.get("headers"):
            headers.update(endpoint_config["headers"])
        
        # Prepare request parameters
        method = endpoint_config.get("method", "GET").upper()
        params = kwargs.get("params", {})
        data = kwargs.get("data")
        json_data = kwargs.get("json")
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                data=data
            )
            response.raise_for_status()
            
            # Try to parse as JSON, fallback to text
            try:
                return {
                    "status_code": response.status_code,
                    "data": response.json(),
                    "success": True
                }
            except json.JSONDecodeError:
                return {
                    "status_code": response.status_code,
                    "data": response.text,
                    "success": True
                }
                
        except httpx.RequestError as e:
            return {
                "status_code": 0,
                "error": f"Request failed: {str(e)}",
                "success": False
            }
        except httpx.HTTPStatusError as e:
            return {
                "status_code": e.response.status_code,
                "error": f"HTTP error: {str(e)}",
                "success": False
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Initialize the MCP server
server = Server("api-integration-server")
api_manager = APIManager()

# Example API configurations - customize these for your APIs
SAMPLE_APIS = [
    APIEndpoint(
        name="jsonplaceholder",
        base_url="https://jsonplaceholder.typicode.com",
        endpoints={
            "get_posts": {
                "path": "/posts",
                "method": "GET",
                "description": "Get all posts"
            },
            "get_post": {
                "path": "/posts/{post_id}",
                "method": "GET",
                "description": "Get a specific post by ID"
            },
            "get_users": {
                "path": "/users",
                "method": "GET",
                "description": "Get all users"
            }
        }
    ),
    # Add your own API configurations here
    APIEndpoint(
        name="weather_api",
        base_url="https://api.openweathermap.org/data/2.5",
        endpoints={
            "current_weather": {
                "path": "/weather",
                "method": "GET",
                "description": "Get current weather for a city"
            },
            "forecast": {
                "path": "/forecast",
                "method": "GET",
                "description": "Get weather forecast"
            }
        },
        headers={"Content-Type": "application/json"}
        # Note: Add your API key in headers or auth_token
    )
]

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools (API endpoints)"""
    tools = []
    
    for api_name, api in api_manager.apis.items():
        for endpoint_name, endpoint_config in api.endpoints.items():
            tool_name = f"{api_name}_{endpoint_name}"
            tools.append(
                types.Tool(
                    name=tool_name,
                    description=f"{api_name}: {endpoint_config.get('description', endpoint_name)}",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "params": {
                                "type": "object",
                                "description": "Query parameters for the API call"
                            },
                            "data": {
                                "type": "object", 
                                "description": "Request body data (for POST/PUT requests)"
                            },
                            "json": {
                                "type": "object",
                                "description": "JSON data for the request"
                            }
                        }
                    }
                )
            )
    
    # Add a general API call tool
    tools.append(
        types.Tool(
            name="call_api",
            description="Make a direct API call to any registered endpoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_name": {
                        "type": "string",
                        "description": "Name of the API to call"
                    },
                    "endpoint_name": {
                        "type": "string", 
                        "description": "Name of the endpoint to call"
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters"
                    },
                    "data": {
                        "type": "object",
                        "description": "Request body data"
                    },
                    "json": {
                        "type": "object",
                        "description": "JSON data for the request"
                    }
                },
                "required": ["api_name", "endpoint_name"]
            }
        )
    )
    
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    try:
        if name == "call_api":
            # Direct API call
            api_name = arguments.get("api_name")
            endpoint_name = arguments.get("endpoint_name")
            params = arguments.get("params", {})
            data = arguments.get("data")
            json_data = arguments.get("json")
            
            result = await api_manager.call_api(
                api_name=api_name,
                endpoint_name=endpoint_name,
                params=params,
                data=data,
                json=json_data
            )
        else:
            # Parse tool name to extract API and endpoint
            if "_" not in name:
                raise ValueError(f"Invalid tool name format: {name}")
            
            api_name, endpoint_name = name.split("_", 1)
            params = arguments.get("params", {})
            data = arguments.get("data")
            json_data = arguments.get("json")
            
            result = await api_manager.call_api(
                api_name=api_name,
                endpoint_name=endpoint_name,
                params=params,
                data=data,
                json=json_data
            )
        
        # Format the result
        if result.get("success"):
            response_text = f"API call successful!\n\nStatus: {result['status_code']}\nResponse:\n{json.dumps(result['data'], indent=2)}"
        else:
            response_text = f"API call failed!\n\nStatus: {result.get('status_code', 'Unknown')}\nError: {result.get('error', 'Unknown error')}"
            
        return [types.TextContent(type="text", text=response_text)]
        
    except Exception as e:
        error_msg = f"Error calling API: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available resources"""
    resources = []
    
    for api_name, api in api_manager.apis.items():
        resources.append(
            types.Resource(
                uri=f"api://{api_name}/info",
                name=f"{api_name} API Info",
                description=f"Information about the {api_name} API endpoints",
                mimeType="application/json"
            )
        )
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read resource content"""
    if uri.startswith("api://"):
        parts = uri.replace("api://", "").split("/")
        if len(parts) >= 2 and parts[1] == "info":
            api_name = parts[0]
            if api_name in api_manager.apis:
                api = api_manager.apis[api_name]
                return json.dumps({
                    "name": api.name,
                    "base_url": api.base_url,
                    "endpoints": api.endpoints
                }, indent=2)
    
    raise ValueError(f"Unknown resource: {uri}")

async def main():
    """Main function to run the MCP server"""
    # Register sample APIs
    for api_config in SAMPLE_APIS:
        api_manager.register_api(api_config)
    
    # You can add your own API configurations here
    # Example:
    # custom_api = APIEndpoint(
    #     name="my_api",
    #     base_url="https://api.example.com/v1",
    #     endpoints={
    #         "get_data": {
    #             "path": "/data",
    #             "method": "GET",
    #             "description": "Get data from my API"
    #         }
    #     },
    #     auth_token="your_api_token_here"
    # )
    # api_manager.register_api(custom_api)
    
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="api-integration-server",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    finally:
        await api_manager.close()

if __name__ == "__main__":
    asyncio.run(main())