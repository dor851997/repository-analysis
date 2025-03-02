import os
import shutil
import time
from fastapi.testclient import TestClient
import pytest

# Import the FastAPI application.
from src.api.endpoints import app

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def cleanup_cloned_repo():
    """
    Fixture to ensure that the cloned repository is removed before and after tests.
    """
    # Remove cloned_repo if exists before tests.
    if os.path.exists("cloned_repo"):
        shutil.rmtree("cloned_repo")
    yield
    # Cleanup after tests.
    if os.path.exists("cloned_repo"):
        shutil.rmtree("cloned_repo")

def test_end_to_end_workflow():
    # 1. Clone a repository using the /clone endpoint.
    clone_payload = {"repo_url": "https://github.com/psf/requests"}
    clone_response = client.post("/clone", json=clone_payload)
    assert clone_response.status_code == 200, f"Clone response failed: {clone_response.text}"
    clone_data = clone_response.json()
    assert clone_data.get("status") == "success", "Clone did not succeed"
    assert "files_processed" in clone_data, "No processed files returned"
    assert len(clone_data["files_processed"]) > 0, "No files were processed"
    
    # Optionally, wait briefly for file processing to complete if needed.
    time.sleep(2)

    # 2. Query the analysis endpoint using the /analyse_repository route.
    rag_payload = {"query": "what can you tell me about the functions in sessions.py?"}
    rag_response = client.post("/analyse_repository", json=rag_payload)
    assert rag_response.status_code == 200, f"Analysis response failed: {rag_response.text}"
    rag_data = rag_response.json()
    assert "response" in rag_data, "No response provided"
    # Optionally, check that the response is not a generic fallback message.
    assert len(rag_data["response"]) > 0, "Empty response received"

    # Print outputs for manual inspection (optional)
    print("Clone Response:", clone_data)
    print("Analysis Response:", rag_data)