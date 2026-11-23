"""Memory service supports isolated persistent CRUD and semantic retrieval."""
import pytest

from app.database.models import Base
from app.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_memory_store_retrieve_update_and_delete(isolated_database):
    async with isolated_database.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    service = MemoryService()
    first = await service.add_memory("Prefers concise explanations", importance=0.8, embedding=[1.0, 0.0])
    await service.add_memory("Likes gardening", importance=0.4, embedding=[0.0, 1.0])
    assert await service.count() == 2

    matches = await service.search_semantic([1.0, 0.0], min_similarity=0.5)
    assert [item["content"] for item in matches] == ["Prefers concise explanations"]
    assert matches[0]["similarity"] == pytest.approx(1.0)
    assert await service.update_memory(first.id, content="Prefers short answers") is True
    assert (await service.get_memory(first.id)).content == "Prefers short answers"
    assert await service.delete_memory(first.id) is True
    assert await service.delete_memory(first.id) is False
    assert await service.count() == 1
