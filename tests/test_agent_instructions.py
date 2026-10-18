from route_agent.agent_factory import AgentsFactory


def test_agente_possui_regras_para_instrucoes_relatorios_e_recomendacoes():
    agente = AgentsFactory.create_agent()
    instrucoes = agente.instructions

    assert "calcular_rota_entrega antes de responder" in instrucoes
    assert "gerar_relatorio_operacional" in instrucoes
    assert "Nao invente horarios" in instrucoes
    assert "metrica ou padrao retornado" in instrucoes
