"""Unit tests — Database models and services."""
import pytest
from app.database.models import Base
from app.services.conversation_service import ConversationService


@pytest.mark.asyncio
async def test_sqlite_conversation_message_crud(isolated_database):
    async with isolated_database.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    service = ConversationService()
    conversation = await service.create_conversation("QA conversation", model_name="test-model")
    message = await service.add_message(conversation.id, "user", "hello", {"source": "test"})
    loaded = await service.get_conversation(conversation.id)
    assert loaded.title == "QA conversation"
    assert loaded.messages[0].content == "hello"
    assert (await service.get_messages(conversation.id))[0].id == message.id
    assert await service.update_conversation(conversation.id, title="Updated") is True
    assert (await service.get_conversation(conversation.id)).title == "Updated"
    assert await service.delete_conversation(conversation.id) is True
    assert await service.get_conversation(conversation.id) is None


def test_database_models_import():
    """Verify all database models can be imported."""
    from app.database.models import Conversation, Message, Memory, Document, Setting, AgentRun
    assert Conversation.__tablename__ == "conversations"
    assert Message.__tablename__ == "messages"
    assert Memory.__tablename__ == "memories"
    assert Document.__tablename__ == "documents"
    assert Setting.__tablename__ == "settings"
    assert AgentRun.__tablename__ == "agent_runs"


def test_conversation_model_has_expected_columns():
    from app.database.models import Conversation
    columns = {c.name for c in Conversation.__table__.columns}
    assert "id" in columns
    assert "title" in columns
    assert "created_at" in columns
    assert "updated_at" in columns
    assert "model_name" in columns
    assert "is_archived" in columns


def test_message_model_has_expected_columns():
    from app.database.models import Message
    columns = {c.name for c in Message.__table__.columns}
    assert "id" in columns
    assert "conversation_id" in columns
    assert "role" in columns
    assert "content" in columns
    assert "created_at" in columns
    assert "metadata" in columns


def test_memory_model_has_expected_columns():
    from app.database.models import Memory
    columns = {c.name for c in Memory.__table__.columns}
    assert "id" in columns
    assert "content" in columns
    assert "summary" in columns
    assert "importance" in columns
    assert "source" in columns
    assert "access_count" in columns


def test_document_model_has_expected_columns():
    from app.database.models import Document
    columns = {c.name for c in Document.__table__.columns}
    assert "id" in columns
    assert "filename" in columns
    assert "file_type" in columns
    assert "chunk_count" in columns
    assert "status" in columns


def test_setting_model_has_expected_columns():
    from app.database.models import Setting
    columns = {c.name for c in Setting.__table__.columns}
    assert "key" in columns
    assert "value" in columns
    assert "updated_at" in columns


def test_engine_module_imports():
    """Verify engine module has required attributes."""
    from app.database.engine import engine, async_session, Base, init_db
    assert engine is not None
    assert async_session is not None
    assert Base is not None
    assert callable(init_db)


def test_services_import():
    """Verify all service classes can be imported."""
    from app.services.conversation_service import ConversationService
    from app.services.memory_service import MemoryService
    from app.services.document_service import DocumentService
    from app.services.settings_service import SettingsService
    from app.services.ollama_service import OllamaService
    assert ConversationService is not None
    assert MemoryService is not None
    assert DocumentService is not None
    assert SettingsService is not None
    assert OllamaService is not None


def test_ollama_service_init():
    """OllamaService initializes with correct base URL."""
    from app.services.ollama_service import OllamaService
    svc = OllamaService(base_url="http://test:11434")
    assert svc.base_url == "http://test:11434"
