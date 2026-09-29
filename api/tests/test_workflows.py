def definition():
    return {"nodes":[
        {"id":"start","type":"start"},
        {"id":"template","type":"template","config":{"template":"你好，{{name}}","output_key":"greeting"}},
        {"id":"end","type":"end","config":{"output":"greeting"}},
    ],"edges":[{"source":"start","target":"template"},{"source":"template","target":"end"}]}


def test_workflow_executes_and_persists_node_trace(client) -> None:
    created=client.post("/api/workflows",json={"name":"Greeting","definition":definition()})
    assert created.status_code==201
    run=client.post(f"/api/workflows/{created.get_json()['id']}/runs",json={"inputs":{"name":"小明"}})
    assert run.status_code==201
    body=run.get_json()
    assert body["status"]=="succeeded"
    assert body["outputs"]["result"]=="你好，小明"
    assert [item["node_id"] for item in body["node_runs"]]==["start","template","end"]


def test_workflow_rejects_cycles(client) -> None:
    invalid={"nodes":[{"id":"start","type":"start"},{"id":"end","type":"end"}],"edges":[{"source":"start","target":"end"},{"source":"end","target":"start"}]}
    assert client.post("/api/workflows",json={"name":"Cycle","definition":invalid}).status_code==400


def test_workflows_are_user_isolated(app) -> None:
    first,second=app.test_client(),app.test_client()
    first.post("/api/auth/register",json={"email":"w1@example.com","password":"password123"})
    second.post("/api/auth/register",json={"email":"w2@example.com","password":"password123"})
    item=first.post("/api/workflows",json={"name":"Private","definition":definition()}).get_json()
    assert second.get("/api/workflows").get_json()["total"]==0
    assert second.get(f"/api/workflows/{item['id']}").status_code==404


def test_condition_selects_matching_branch(client) -> None:
    graph={"nodes":[
        {"id":"start","type":"start"},
        {"id":"condition","type":"condition","config":{"variable":"approved","value":True}},
        {"id":"yes","type":"template","config":{"template":"通过","output_key":"result"}},
        {"id":"no","type":"template","config":{"template":"拒绝","output_key":"result"}},
        {"id":"end","type":"end","config":{"output":"result"}},
    ],"edges":[{"source":"start","target":"condition"},{"source":"condition","target":"yes","condition":"true"},{"source":"condition","target":"no","condition":"false"},{"source":"yes","target":"end"},{"source":"no","target":"end"}]}
    workflow=client.post("/api/workflows",json={"name":"Branch","definition":graph}).get_json()
    run=client.post(f"/api/workflows/{workflow['id']}/runs",json={"inputs":{"approved":True}}).get_json()
    assert run["outputs"]["result"]=="通过"
