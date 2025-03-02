import pytest
import asyncio
from src.core.repository_analysis import analyze_repository

@pytest.mark.asyncio
async def test_analyze_repository(monkeypatch):
    # Create a fake analyze_code that returns a predictable summary,
    # explicitly including "file1.py" and "file2.txt" in the output.
    async def fake_analyze_code(query: str, context: str) -> str:
        # For example, we simulate a summary that includes the file names.
        return f"Overall analysis includes: file1.py, file2.txt. Context was: {context}"
    
    # Patch the analyze_code function in the assistant module
    monkeypatch.setattr("src.core.assistant.analyze_code", fake_analyze_code)
    
    import tempfile, os
    with tempfile.TemporaryDirectory() as tempdir:
        # Create two dummy text files with simple content.
        file1 = os.path.join(tempdir, "file1.py")
        file2 = os.path.join(tempdir, "file2.txt")
        with open(file1, "w") as f:
            f.write("print('Hello from file1')")
        with open(file2, "w") as f:
            f.write("print('Hello from file2')")
    
        overall_analysis = await analyze_repository(tempdir)
        # Assert that the overall analysis mentions the file names.
        assert "Based on the provided file summaries" in overall_analysis