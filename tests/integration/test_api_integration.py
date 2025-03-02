import os
import shutil
import time
import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application.
from src.api.endpoints import app

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def cleanup_cloned_repo():
    """
    Fixture to ensure that the cloned repository folder is removed before and after tests.
    """
    # Remove cloned_repo folder if it exists.
    if os.path.exists("cloned_repo"):
        shutil.rmtree("cloned_repo")
    yield
    if os.path.exists("cloned_repo"):
        shutil.rmtree("cloned_repo")

def test_clone_endpoint():
    """
    Test the /clone endpoint by cloning a repository and checking that files are processed.
    """
    clone_payload = {"repo_url": "https://github.com/psf/requests"}
    response = client.post("/clone", json=clone_payload)
    assert response.status_code == 200, f"Clone failed: {response.text}"
    data = response.json()
    assert data.get("status") == "success", "Clone did not succeed"
    files = data.get("files_processed", [])
    assert len(files) > 0, "No files were processed"
    print("Clone endpoint response:", data)

def test_analyse_repository_endpoint():
    """
    Test the /analyse_repository endpoint by sending a query about the repository.
    """
    # Ensure that the clone has had a moment to complete file processing.
    time.sleep(2)
    analysis_payload = {"query": "What can you tell me about the repository?"}
    response = client.post("/analyse_repository", json=analysis_payload)
    assert response.status_code == 200, f"Analysis endpoint failed: {response.text}"
    data = response.json()
    assert "response" in data, "Response key missing"
    assert len(data["response"]) > 0, "Empty response received"
    print("Analyse repository endpoint response:", data)