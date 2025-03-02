# src/core/repository_analysis.py

import os
import asyncio
import aiofiles
from pathlib import Path
from src.core.assistant import analyze_code

def is_text_file(file_path: Path) -> bool:
    """Simple heuristic to filter text files (adjust as needed)."""
    # Process common code file extensions; skip binary files and .git
    text_extensions = {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.html', '.css', '.md', '.txt'}
    return file_path.suffix in text_extensions

async def analyze_repository(repo_path: str) -> str:
    """
    Analyze all text files in the repository and produce an overall analysis.
    """
    base_path = Path(repo_path)
    summaries = []

    # Walk through the repository, skipping .git directory
    for root, dirs, files in os.walk(base_path):
        # Skip .git directory
        if ".git" in dirs:
            dirs.remove(".git")
        for file in files:
            file_path = Path(root) / file
            if not is_text_file(file_path):
                continue  # Skip non-text files
            
            try:
                async with aiofiles.open(file_path, mode='r') as f:
                    content = await f.read()
                
                # Generate a brief summary for the file
                file_summary = await analyze_code("Summarize this file", content)
                summaries.append(f"File {file_path} summary: {file_summary}")
            except Exception as e:
                # Log the error or skip files that cause issues
                continue

    # Combine all individual summaries into one prompt
    aggregated_summary = "\n".join(summaries)
    overall_analysis = await analyze_code(
        "Based on the following file summaries, provide an overall analysis of the project:",
        aggregated_summary
    )
    return overall_analysis