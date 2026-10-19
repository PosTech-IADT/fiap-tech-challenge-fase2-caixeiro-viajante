from route_agent.mcp_manager import MCPManager


def test_route_assistant_nao_recebe_tool_descontinuada():
    servidor = MCPManager.get_server()

    assert servidor.tool_filter == {
        "blocked_tool_names": ["calcular_rota_entrega"],
    }
