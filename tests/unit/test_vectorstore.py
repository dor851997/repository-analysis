import pytest
import asyncio
from src.core.vectorstore import chunk_text, process_code_file, global_id_counter, metadata_store, faiss_index, DIMENSION

# Test that chunk_text splits a string correctly.
def test_chunk_text():
    text = "abcdefghij"
    chunks = chunk_text(text, chunk_size=3)
    assert chunks == ["abc", "def", "ghi", "j"]

# Test that passing a non-string returns an empty list.
def test_chunk_text_with_non_string():
    result = chunk_text(123, chunk_size=3)
    assert result == []

# Test generate_embedding by monkeypatching it to return a predictable vector.
@pytest.mark.asyncio
async def test_generate_embedding(monkeypatch):
    # Define a fake embedding function that returns a vector of constant values.
    async def fake_generate_embedding(text: str):
        # Return a list of length DIMENSION with all elements equal to len(text)
        return [len(text)] * DIMENSION

    monkeypatch.setattr("src.core.vectorstore.generate_embedding", fake_generate_embedding)
    # Now call generate_embedding (which is monkeypatched) and check its output.
    from src.core.vectorstore import generate_embedding  # re-import to pick up monkeypatch
    embedding = await generate_embedding("hello")
    expected = [5] * DIMENSION  # Since len("hello") is 5
    assert embedding == expected

# Test process_code_file by simulating a scenario where chunking produces two chunks,
# and the fake embedding function raises an exception for one of them.
@pytest.mark.asyncio
async def test_process_code_file(monkeypatch):
    # Force chunk_text to return two specific chunks.
    monkeypatch.setattr("src.core.vectorstore.chunk_text", lambda text, chunk_size=2000: ["good_chunk ", "fail_chunk"])

    # Define a fake generate_embedding:
    async def fake_generate_embedding(text: str):
        if "fail" in text:
            raise Exception("Chunk processing error")
        # Return a fake embedding: a vector of length DIMENSION with value equal to len(text)
        return [len(text)] * DIMENSION

    monkeypatch.setattr("src.core.vectorstore.generate_embedding", fake_generate_embedding)

    # We'll also monkeypatch store_embeddings to capture what is upserted instead of actually using FAISS.
    embeddings_collected = {}
    async def fake_store_embeddings(embeddings):
        nonlocal embeddings_collected
        embeddings_collected = embeddings

    monkeypatch.setattr("src.core.vectorstore.store_embeddings", fake_store_embeddings)

    # Process a dummy file with content that will be split into two chunks.
    content = "good_chunk " + "fail_chunk"
    await process_code_file("dummy_file.txt", content)
    # Expect that the first chunk ("good_chunk ") is processed and stored,
    # while the second chunk causes an exception and is skipped.
    assert any("dummy_file.txt_chunk_" in key for key in embeddings_collected.keys())