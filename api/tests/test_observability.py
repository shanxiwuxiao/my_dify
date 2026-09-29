def test_model_calls_are_recorded(client) -> None:
    app=client.post("/api/apps",json={"name":"Observed"}).get_json()
    client.post(f"/api/apps/{app['id']}/chat",json={"message":"hello"})
    summary=client.get("/api/monitoring/summary").get_json()
    assert summary["total_calls"]==1
    assert summary["failed_calls"]==0
    assert summary["input_chars"]>0
    assert summary["output_chars"]>0


def test_evaluation_dataset_runs_against_application(client) -> None:
    app=client.post("/api/apps",json={"name":"Evaluated"}).get_json()
    dataset=client.post("/api/evaluation-datasets",json={"name":"Smoke"}).get_json()
    case=client.post(f"/api/evaluation-datasets/{dataset['id']}/cases",json={"input":"hello","expected":"hello"}).get_json()
    client.post(f"/api/evaluation-datasets/{dataset['id']}/cases",json={"input":"world","expected":"missing"})
    run=client.post(f"/api/evaluation-datasets/{dataset['id']}/runs",json={"app_id":app["id"]})
    assert run.status_code==201
    assert run.get_json()["total"]==2
    assert run.get_json()["passed"]==1
    assert run.get_json()["pass_rate"]==0.5
    assert client.get(f"/api/evaluation-datasets/{dataset['id']}/runs").get_json()["total"]==1
    assert client.delete(f"/api/evaluation-datasets/{dataset['id']}/cases/{case['id']}").status_code==204


def test_monitoring_and_datasets_are_user_isolated(app) -> None:
    first,second=app.test_client(),app.test_client()
    first.post("/api/auth/register",json={"email":"o1@example.com","password":"password123"})
    second.post("/api/auth/register",json={"email":"o2@example.com","password":"password123"})
    first.post("/api/evaluation-datasets",json={"name":"Private"})
    assert second.get("/api/evaluation-datasets").get_json()["total"]==0
