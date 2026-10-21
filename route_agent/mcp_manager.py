import os

from agents.mcp.server import MCPServerSse


class MCPManager:
    @staticmethod
    def get_server():
        timeout_seconds = float(
            os.getenv("MCP_CLIENT_TIMEOUT_SECONDS", "300")
        )

        return MCPServerSse(
            {
                "url": os.getenv(
                    "MCP_SERVER_URL",
                    "http://mcp-server:8000/sse",
                )
            },
            cache_tools_list=True,
            name="FIAP Route MCP",
            client_session_timeout_seconds=timeout_seconds,
            tool_filter={
                "blocked_tool_names": ["calcular_rota_entrega"],
            },
        )
