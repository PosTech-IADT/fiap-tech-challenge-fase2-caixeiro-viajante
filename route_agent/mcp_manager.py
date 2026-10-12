import os

from agents.mcp.server import MCPServerSse


class MCPManager:
    @staticmethod
    def get_server():
        return MCPServerSse(
            {
                "url": os.getenv(
                    "MCP_SERVER_URL",
                    "http://mcp-server:8000/sse",
                )
            },
            cache_tools_list=True,
            name="FIAP Route MCP",
            client_session_timeout_seconds=180,
        )
