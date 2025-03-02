from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from pathlib import Path
import asyncio
import time
import psutil
import logging

# ---------------------- Logging Setup ----------------------
logger = logging.getLogger("endpoints")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = FastAPI()

# ---------------------- Middleware ----------------------
@app.middleware("http")
async def log_request_data(request: Request, call_next):
    """
    Middleware that logs the duration and memory usage for each incoming HTTP request.
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    # Get current memory usage in MB.
    process = psutil.Process()
    mem_usage = process.memory_info().rss / (1024 * 1024)

    logger.info(f"Path: {request.url.path} | Duration: {duration:.4f}s | Memory Usage: {mem_usage:.2f} MB")
    response.headers["X-Process-Time"] = f"{duration:.4f}"
    response.headers["X-Memory-Usage-MB"] = f"{mem_usage:.2f}"
    return response

# ---------------------- Pydantic Models ----------------------
class CloneRequest(BaseModel):
    repo_url: str

class RagRequest(BaseModel):
    query: str

# ---------------------- Core Module Imports ----------------------
from src.core import repository, assistant

# ---------------------- Endpoints ----------------------
@app.post("/clone")
async def clone_repo(request: CloneRequest):
    """
    Clone a Git repository based on the provided GitHub URL.
    This endpoint removes any existing cloned repository, clones the new one, and processes its files.
    
    Returns:
        A JSON object with the status and list of processed files.
    """
    target_dir = Path("cloned_repo")
    try:
        await repository.clone_repository(request.repo_url, target_dir)
        files = await repository.process_files(target_dir)
        return {"status": "success", "files_processed": [str(f) for f in files]}
    except Exception as e:
        logger.error("Error in /clone: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyse_repository")
async def analyse_repository_endpoint(request: RagRequest):
    """
    Answer queries about the repository or specific files using a retrieval-augmented generation (RAG) approach.
    
    The system detects if a file name is mentioned in the query (e.g., "sessions.py") and, if so, retrieves the full content of that file.
    Otherwise, it uses the FAISS-based retrieval mechanism to gather context.
    
    Returns:
        A JSON object with the LLM-generated response.
    """
    try:
        # Simply pass the query; file-filtering logic is handled in assistant.generate_rag_response.
        response = await assistant.generate_rag_response(request.query)
        return {"response": response}
    except Exception as e:
        logger.error("Error in /analyse_repository: %s", e)
        raise HTTPException(status_code=500, detail=str(e))