import sys
import os
import shutil
import asyncio
from pathlib import Path
import aiofiles
import logging

# Add project root to sys.path so that src modules can be imported.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.performance import measure_time
from src.core.vectorstore import process_code_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

@measure_time
async def clone_repository(repo_url: str, target_dir: Path) -> None:
    """
    Clone a Git repository asynchronously.
    If the target directory already exists, it is removed and re-cloned.
    """
    if target_dir.exists():
        print(f"Target directory {target_dir} already exists. Removing it...")
        shutil.rmtree(target_dir)
    
    process = await asyncio.create_subprocess_exec(
        'git', 'clone', repo_url, str(target_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(f"Error cloning repository: {stderr.decode().strip()}")
    print(f"Repository cloned to {target_dir}")

@measure_time
async def process_files(repo_dir: Path) -> list:
    """
    Process all eligible files in the repository and return a list of processed file paths.
    Eligible files include those with extensions .py, .txt, or .md.
    """
    processed_files = []
    for file_path in repo_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in ['.py', '.txt', '.md']:
            try:
                async with aiofiles.open(file_path, mode='r') as f:
                    content = await f.read()
                await process_code_file(str(file_path), content)
                processed_files.append(file_path)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
    return processed_files

@measure_time
async def clone_and_process_repository(repo_url: str, target_dir: str) -> None:
    """
    Clone the repository and process eligible files.
    This function removes any existing FAISS index and metadata files and resets the in-memory state.
    """
    # Remove existing FAISS index and metadata files.
    faiss_index_file = os.environ.get("FAISS_INDEX_FILE", "faiss_index.idx")
    metadata_file = os.environ.get("FAISS_METADATA_FILE", "faiss_metadata.json")
    if os.path.exists(faiss_index_file):
        os.remove(faiss_index_file)
        print(f"Removed old FAISS index: {faiss_index_file}")
    if os.path.exists(metadata_file):
        os.remove(metadata_file)
        print(f"Removed old metadata file: {metadata_file}")
    
    # Reset in-memory state in vectorstore.
    from src.core import vectorstore
    vectorstore.metadata_store.clear()
    vectorstore.global_id_counter = 0
    import faiss
    vectorstore.faiss_index = faiss.IndexFlatL2(vectorstore.DIMENSION)
    print("Cleared in-memory vectorstore state.")

    target_path = Path(target_dir)
    await clone_repository(repo_url, target_path)
    processed_files = await process_files(target_path)
    print("Processed files:")
    for f in processed_files:
        print(str(f))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python repository.py <repo_url> <target_dir>")
        sys.exit(1)
    repo_url = sys.argv[1]
    target_dir = sys.argv[2]
    asyncio.run(clone_and_process_repository(repo_url, target_dir))