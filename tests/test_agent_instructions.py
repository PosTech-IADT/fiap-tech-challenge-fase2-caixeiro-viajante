from route_agent.agent_factory import AgentsFactory


def test_agente_possui_regras_para_instrucoes_relatorios_e_recomendacoes():
    agente = AgentsFactory.create_agent()
    instrucoes = agente.instructions

    assert "otimizar_rota_genetica" in instrucoes
    assert "converta criticidade alta para prioridade" in instrucoes
    assert "Nunca use calcular_rota_entrega" in instrucoes
    assert "otimizar_rota_genetica antes de responder" in instrucoes
    assert "gerar_relatorio_operacional" in instrucoes
    assert "Nao invente horarios" in instrucoes
    assert "metrica ou padrao retornado" in instrucoes


def test_agente_usa_gpt_5_4_mini_com_raciocinio_baixo():
    agente = AgentsFactory.create_agent()

    assert agente.model == "gpt-5.4-mini"
    assert agente.model_settings.reasoning.effort == "low"
    assert agente.model_settings.verbosity == "low"
    assert agente.model_settings.temperature is None
    assert agente.model_settings.parallel_tool_calls is False
