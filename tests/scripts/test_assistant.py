import sys
import os
import asyncio

# Adjust the path so we can import from src/
# This goes up two levels from tests/scripts to the project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.assistant import generate_rag_response

# Example test function
async def test_rag_for_assistant():
    query = "What can you tell me about the full repository?"
    response = await generate_rag_response(query)
    print("Query:", query)
    print("Response:", response)

if __name__ == "__main__":
    asyncio.run(test_rag_for_assistant())