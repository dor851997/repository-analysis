import os
import time
import shutil
import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application.
from src.api.endpoints import app

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def cleanup_cloned_repo():
    """
    Fixture to remove the cloned repository before and after tests.
    """
    if os.path.exists("cloned_repo"):
        shutil.rmtree("cloned_repo")
    yield
    if os.path.exists("cloned_repo"):
        shutil.rmtree("cloned_repo")

def test_performance_clone_endpoint():
    """
    Test the performance of the /clone endpoint.
    Verifies that the endpoint returns the expected telemetry headers.
    """
    clone_payload = {"repo_url": "https://github.com/psf/requests"}
    start_time = time.time()
    response = client.post("/clone", json=clone_payload)
    elapsed = time.time() - start_time

    assert response.status_code == 200, f"Clone failed: {response.text}"
    
    # Check that the telemetry headers are present.
    process_time = response.headers.get("X-Process-Time")
    memory_usage = response.headers.get("X-Memory-Usage-MB")
    assert process_time is not None, "X-Process-Time header missing"
    assert memory_usage is not None, "X-Memory-Usage-MB header missing"
    
    print(f"/clone endpoint: Process Time Header: {process_time}s, Memory Usage Header: {memory_usage}MB, Total Elapsed: {elapsed:.4f}s")

def test_performance_analyse_repository_endpoint():
    """
    Test the performance of the /analyse_repository endpoint.
    Ensures that the telemetry headers are returned and logs the duration.
    """
    # Ensure that the repository is already cloned.
    clone_payload = {"repo_url": "https://github.com/psf/requests"}
    client.post("/clone", json=clone_payload)
    time.sleep(2)  # Give time for file processing

    analysis_payload = {"query": "What can you tell me about the repository?"}
    start_time = time.time()
    response = client.post("/analyse_repository", json=analysis_payload)
    elapsed = time.time() - start_time

    assert response.status_code == 200, f"Analysis endpoint failed: {response.text}"

    process_time = response.headers.get("X-Process-Time")
    memory_usage = response.headers.get("X-Memory-Usage-MB")
    assert process_time is not None, "X-Process-Time header missing"
    assert memory_usage is not None, "X-Memory-Usage-MB header missing"

    print(f"/analyse_repository endpoint: Process Time Header: {process_time}s, Memory Usage Header: {memory_usage}MB, Total Elapsed: {elapsed:.4f}s")