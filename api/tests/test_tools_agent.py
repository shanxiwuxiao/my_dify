import json


def test_calculator_tool_is_safe(client) -> None:
    from flask import current_app
    with current_app.app_context() if False else client.application.app_context():
        tools=client.application.extensions["tool_service"]
        assert tools.invoke("calculator",{"expression":"(2 + 3) * 4"})["result"]==20
        try:tools.invoke("calculator",{"expression":"__import__('os').system('x')"})
        except Exception:pass
        else:raise AssertionError("unsafe expression was accepted")


def test_agent_returns_plain_model_answer_when_not_tool_json(client) -> None:
    app=client.post("/api/apps",json={"name":"Agent"}).get_json()
    response=client.post(f"/api/apps/{app['id']}/agent",json={"query":"你好"})
    assert response.status_code==200
    assert response.get_json()["answer"].startswith("Fake answer:")
    assert response.get_json()["trace"]==[]


def test_tool_node_runs_in_workflow(client) -> None:
    graph={"nodes":[{"id":"start","type":"start"},{"id":"calc","type":"tool","config":{"name":"calculator","arguments":{"expression":"{{expression}}"},"output_key":"calculation"}},{"id":"end","type":"end","config":{"output":"calculation"}}],"edges":[{"source":"start","target":"calc"},{"source":"calc","target":"end"}]}
    workflow=client.post("/api/workflows",json={"name":"Calculator","definition":graph}).get_json()
    run=client.post(f"/api/workflows/{workflow['id']}/runs",json={"inputs":{"expression":"6*7"}}).get_json()
    assert run["outputs"]["result"]=={"result":42}
