import pytest
from fastapi.testclient import TestClient
from src.api.endpoints import app
import tempfile
import os

client = TestClient(app)

def test_clone_endpoint(monkeypatch):
    async def fake_clone(repo_url, target_dir):
        # Simulate cloning by creating a dummy directory with one file.
        import os
        os.makedirs(str(target_dir), exist_ok=True)
        with open(target_dir / "README", "w") as f:
            f.write("Hello World!")
    
    monkeypatch.setattr("src.core.repository.clone_repository", fake_clone)
    response = client.post("/clone", json={"repo_url": "https://github.com/octocat/Hello-World.git"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "success"

def test_analyze_endpoint(monkeypatch):
    async def fake_analyze(query, context):
        return "Fake analysis: code does X."
    
    # Patch the analyze_code function in the repository_analysis module,
    # since /analyze endpoint calls repository_analysis.analyze_code.
    import src.core.repository_analysis as repository_analysis
    monkeypatch.setattr(repository_analysis, "analyze_code", fake_analyze)
    
    # Create a temporary file with some simple code.
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write("print('Hello')")
        tmp_path = tmp.name
    
    response = client.post("/analyze", json={
        "query": "What does this code do?",
        "file_path": tmp_path
    })
    
    if response.status_code != 200:
        print("Error response:", response.json())
    
    assert response.status_code == 200
    data = response.json()
    assert data.get("analysis") == "Fake analysis: code does X."
    
    # Clean up the temporary file.
    os.remove(tmp_path)

def test_analyze_repo_endpoint(monkeypatch):
    async def fake_analyze_repository(repo_path: str) -> str:
        return "Overall repository analysis."
    
    import src.core.repository_analysis as repository_analysis
    monkeypatch.setattr(repository_analysis, "analyze_repository", fake_analyze_repository)
    response = client.post("/analyze_repo", json={"repo_path": "dummy_repo_path"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("analysis") == "Overall repository analysis."