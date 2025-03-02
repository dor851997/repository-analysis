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

async def run_vectorstore_test():
    # Example usage: process a file and query the index
    file_path = "test_file.txt"
    content = "This is some test content for vectorstore."
    await process_code_file(file_path, content)
    
    print("Number of vectors in FAISS index:", faiss_index.ntotal)
    print("Metadata store:", metadata_store)

if __name__ == "__main__":
    asyncio.run(run_vectorstore_test())