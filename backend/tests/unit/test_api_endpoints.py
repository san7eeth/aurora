"""Unit tests — FastAPI REST endpoints (v0.3.0)."""


def test_health_returns_200(test_client):
    r = test_client.get("/health")
    assert r.status_code == 200


def test_health_body_has_status_ok(test_client):
    r = test_client.get("/health")
    assert r.json()["status"] == "ok"


def test_health_body_has_model(test_client):
    r = test_client.get("/health")
    assert "model" in r.json()


def test_health_body_has_version(test_client):
    r = test_client.get("/health")
    assert r.json()["version"] == "0.3.0"


def test_health_reports_database_and_ollama(test_client):
    body = test_client.get("/health").json()
    assert body["database"] == "ok"
    assert body["ollama"] is True
    assert body["status"] == "ok"


def test_select_model_empty_name_returns_400(test_client):
    r = test_client.post("/api/models/select", json={"model": ""})
    assert r.status_code == 400
    assert "error" in r.json()


def test_select_model_valid_name_returns_200(test_client):
    r = test_client.post("/api/models/select", json={"model": "phi3:mini"})
    assert r.status_code == 200
    assert r.json()["active"] == "phi3:mini"


def test_select_model_missing_body_returns_400(test_client):
    r = test_client.post("/api/models/select", json={})
    assert r.status_code == 400


# --- Conversation endpoints ---

def test_list_conversations_returns_200(test_client):
    r = test_client.get("/api/conversations")
    assert r.status_code == 200
    assert "conversations" in r.json()


def test_create_conversation(test_client):
    r = test_client.post("/api/conversations", json={"title": "Test Chat"})
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["title"] == "Test Chat"


def test_get_nonexistent_conversation_returns_404(test_client):
    r = test_client.get("/api/conversations/nonexistent-id")
    assert r.status_code == 404


def test_delete_nonexistent_conversation_returns_404(test_client):
    r = test_client.delete("/api/conversations/nonexistent-id")
    assert r.status_code == 404


# --- Memory endpoints ---

def test_list_memories_returns_200(test_client):
    r = test_client.get("/api/memories")
    assert r.status_code == 200
    assert "memories" in r.json()


def test_add_memory_requires_content(test_client):
    r = test_client.post("/api/memories", json={"content": ""})
    assert r.status_code == 400


def test_add_memory_success(test_client):
    r = test_client.post("/api/memories", json={"content": "User prefers dark mode"})
    assert r.status_code == 200
    assert "id" in r.json()


# --- Document endpoints ---

def test_list_documents_returns_200(test_client):
    r = test_client.get("/api/documents")
    assert r.status_code == 200
    assert "documents" in r.json()


# --- Settings endpoints ---

def test_get_settings_returns_200(test_client):
    r = test_client.get("/api/settings")
    assert r.status_code == 200
    assert "settings" in r.json()


def test_metrics_exposes_request_counters(test_client):
    response = test_client.get("/metrics")
    assert response.status_code == 200
    assert "aurora_http_requests_total" in response.text


def test_voice_profile_cannot_be_written_through_general_settings(test_client):
    response = test_client.post("/api/settings", json={"voice_auth_profile": {"embedding": [1]}})
    assert response.status_code == 400


def test_agent_execution_requires_explicit_confirmation(test_client):
    response = test_client.post("/api/agent/execute", json={"plan_id": "does-not-exist", "confirmed": False})
    assert response.status_code == 400


def test_agent_tool_registry_returns_allowlisted_tools(test_client):
    response = test_client.get("/api/agent/tools")
    assert response.status_code == 200
    assert {tool["name"] for tool in response.json()["tools"]} == {
        "system_info", "list_files", "launch_app", "clipboard_read"
    }


def test_update_settings(test_client):
    r = test_client.post("/api/settings", json={"theme": "dark", "language": "en"})
    assert r.status_code == 200


# --- Chat REST endpoint ---

def test_chat_requires_message(test_client):
    r = test_client.post("/api/chat", json={"message": ""})
    assert r.status_code == 400


def test_chat_rest_returns_response(test_client):
    r = test_client.post("/api/chat", json={"message": "Hello"})
    assert r.status_code == 200
    data = r.json()
    assert "response" in data
    assert "conversation_id" in data
