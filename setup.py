from setuptools import setup, find_packages

setup(
    name="mcp-api-server",
    version="1.0.0",
    description="MCP Server with API Integration",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.0.0",
        "httpx>=0.25.0", 
        "pydantic>=2.0.0",
        "asyncio-mqtt",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "mcp-api-server=mcp_server:main",
        ],
    },
)