def create_knowledge(client):
    return client.post("/api/knowledge-bases", json={"name": "Python 文档"}).get_json()


def test_document_is_chunked_and_searchable(client) -> None:
    knowledge = create_knowledge(client)
    document = client.post(f"/api/knowledge-bases/{knowledge['id']}/documents", json={
        "name": "decorator.md",
        "content": "Python 装饰器可以在不修改函数源码的情况下增强函数行为。" * 80,
    })
    assert document.status_code == 201
    assert client.get(f"/api/knowledge-bases/{knowledge['id']}/documents").get_json()["total"] == 1
    results = client.post(f"/api/knowledge-bases/{knowledge['id']}/search", json={"query": "Python 装饰器", "top_k": 2}).get_json()["items"]
    assert results
    assert results[0]["document_name"] == "decorator.md"
    assert "装饰器" in results[0]["content"]
    assert client.delete(f"/api/knowledge-bases/{knowledge['id']}/documents/{document.get_json()['id']}").status_code == 204
    assert client.get(f"/api/knowledge-bases/{knowledge['id']}/documents").get_json()["total"] == 0


def test_knowledge_is_isolated_and_can_bind_to_owned_app(app) -> None:
    first, second = app.test_client(), app.test_client()
    first.post("/api/auth/register", json={"email": "k1@example.com", "password": "password123"})
    second.post("/api/auth/register", json={"email": "k2@example.com", "password": "password123"})
    knowledge = first.post("/api/knowledge-bases", json={"name": "Private"}).get_json()
    application = first.post("/api/apps", json={"name": "RAG"}).get_json()
    assert first.put(f"/api/apps/{application['id']}/knowledge-bases", json={"knowledge_base_ids": [knowledge['id']]}).status_code == 200
    assert second.get(f"/api/knowledge-bases/{knowledge['id']}/documents").status_code == 404


def test_conversation_chat_injects_retrieved_context(client, model_client) -> None:
    knowledge = create_knowledge(client)
    client.post(f"/api/knowledge-bases/{knowledge['id']}/documents", json={"name": "facts.txt", "content": "my_dify 的暗号是蓝鲸。"})
    application = client.post("/api/apps", json={"name": "RAG app", "system_prompt": "回答问题"}).get_json()
    client.put(f"/api/apps/{application['id']}/knowledge-bases", json={"knowledge_base_ids": [knowledge['id']]})
    conversation = client.post(f"/api/apps/{application['id']}/conversations", json={}).get_json()
    response = client.post(f"/api/conversations/{conversation['id']}/messages", json={"message": "暗号是什么？"})
    assert response.status_code == 200
    assert response.get_json()["sources"][0]["document_name"] == "facts.txt"
    assert "蓝鲸" in model_client.messages[0]["content"]
