import sys
import os
import asyncio

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.vectorstore import (
    faiss_index,
    metadata_store,
    generate_embedding,
    process_code_file
)

async def test_faiss_integration():
    # Example test: create embeddings for a dummy file, store them, verify they appear in faiss_index
    file_path = "dummy_file.py"
    content = "print('Hello from a dummy file')"
    await process_code_file(file_path, content)
    
    # Check how many vectors we have
    print("FAISS index total vectors:", faiss_index.ntotal)
    print("Metadata store contents:", metadata_store)

if __name__ == "__main__":
    asyncio.run(test_faiss_integration())