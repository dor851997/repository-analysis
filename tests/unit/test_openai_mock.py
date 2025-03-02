import asyncio
import pytest
from src.core.assistant import analyze_code, generate_rag_response

# Dummy classes to simulate OpenAI API response structure.
class DummyChoice:
    def __init__(self, message):
        self.message = message

class DummyResponse:
    def __init__(self, content: str):
        # Mimic the structure: response.choices[0].message.content
        self.choices = [DummyChoice(message={"content": content})]

# Dummy async function to simulate a successful API call.
async def dummy_chat_create(*args, **kwargs):
    # For testing, always return this dummy response.
    return DummyResponse("Mocked API response")

# Dummy functions to simulate embedding and FAISS retrieval if needed.
async def dummy_generate_embedding(query: str):
    # Return a dummy embedding (a list of floats)
    return [0.1, 0.2, 0.3]

def dummy_query_faiss(embedding, k: int):
    # Return a dummy structure with indices and distances.
    # Assume that our metadata_store has at least one entry.
    return {
        "indices": [[0] * k],
        "distances": [[0.6] * k]
    }

# For testing, we can also simulate a minimal metadata_store.
dummy_metadata_store = {
    0: {"file_chunk_id": "dummy_file.py_chunk_0", "chunk_text": "def dummy_function(): pass"}
}

# Patch the vectorstore functions used by generate_rag_response.
@pytest.fixture(autouse=True)
def patch_vectorstore(monkeypatch):
    monkeypatch.setattr("src.core.assistant.generate_embedding", dummy_generate_embedding)
    monkeypatch.setattr("src.core.assistant.query_faiss", dummy_query_faiss)
    # Also override metadata_store to use our dummy value.
    monkeypatch.setattr("src.core.assistant.metadata_store", dummy_metadata_store)

@pytest.mark.asyncio
async def test_analyze_code(monkeypatch):
    # Mock the OpenAI API call in analyze_code.
    monkeypatch.setattr("src.core.assistant.aclient.chat.completions.create", dummy_chat_create)
    result = await analyze_code("dummy query", "dummy code context")
    assert "Mocked API response" in result

@pytest.mark.asyncio
async def test_generate_rag_response(monkeypatch):
    # For a file-specific query, ensure that full file content is used.
    # We simulate that a file named "dummy_file.py" exists in the cloned_repo.
    # We'll monkeypatch read_file_content to return a dummy file content.
    async def dummy_read_file_content(file_path: str) -> str:
        return "def dummy_function():\n    return 'Hello, World!'"
    monkeypatch.setattr("src.core.assistant.read_file_content", dummy_read_file_content)
    # Also mock the OpenAI API call.
    monkeypatch.setattr("src.core.assistant.aclient.chat.completions.create", dummy_chat_create)

    # Query that mentions a file.
    query = "What can you tell me about dummy_file.py?"
    result = await generate_rag_response(query)
    # Since file-specific queries use full file content exclusively, our dummy response should be returned.
    assert "Mocked API response" in result

    # For a generic query, since FAISS retrieval is used, the dummy metadata_store is used.
    query_generic = "Tell me about the repository"
    result_generic = await generate_rag_response(query_generic)
    assert "Mocked API response" in result_generic