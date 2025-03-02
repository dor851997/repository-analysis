from dotenv import load_dotenv
load_dotenv()

import os
import re
import asyncio
import logging
import time
import functools
from pathlib import Path
from typing import List, Dict, Any
import aiofiles
import openai
from openai import AsyncOpenAI
from src.core.vectorstore import query_faiss, metadata_store, generate_embedding
from src.utils.rate_limiter import AsyncRateLimiter

# ---------------------- Performance Monitoring ----------------------
def measure_time(func):
    """Async decorator to measure execution time of functions."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logging.getLogger(__name__).info(f"{func.__name__} took {elapsed:.4f} seconds")
        return result
    return wrapper

# ---------------------- Logging Configuration ----------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# ---------------------- OpenAI Async Client ----------------------
aclient = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------------------- Core Functions ----------------------
async def analyze_code(query: str, context: str) -> str:
    try:
        response = await aclient.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "You are an expert code reviewer. Provide a comprehensive analysis of the provided code. "
                    "Discuss functionality, design, error handling, and potential improvements."
                )},
                {"role": "user", "content": f"Code context:\n{context}\n\nQuestion: {query}"}
            ],
            temperature=0.2,
            max_tokens=600
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Error in analyze_code: %s", e)
        return f"Error calling OpenAI API: {e}"

async def analyze_code_with_context(conversation_history: List[Dict[str, str]]) -> str:
    try:
        messages = [
            {"role": "system", "content": (
                "You are an expert code reviewer. Engage in a multi-turn conversation, "
                "using the provided conversation history to provide detailed, technical responses."
            )}
        ]
        messages.extend(conversation_history)
        response = await aclient.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.2,
            max_tokens=600
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Error in analyze_code_with_context: %s", e)
        return f"Error calling OpenAI API: {e}"

async def get_unique_file_names() -> List[str]:
    file_names = set()
    for meta in metadata_store.values():
        file_chunk_id = meta.get("file_chunk_id", "")
        m = re.match(r"(.*)_chunk_\d+", file_chunk_id)
        if m:
            file_names.add(m.group(1))
        else:
            file_names.add(file_chunk_id)
    return list(file_names)

async def infer_filter_from_query(user_query: str, available_files: List[str]) -> str:
    prompt = (
        f"Available files: {', '.join(available_files)}\n"
        f"User Query: '{user_query}'\n"
        "Based on these, provide a single keyword that best represents the subset of files most relevant "
        "to the query. If the query is about the full repository, respond with 'all'."
    )
    
    response = await aclient.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert at extracting relevant keywords from a user query based on available file names."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=10
    )
    keyword = response.choices[0].message.content.strip()
    if keyword.lower() == "all":
        return None
    return keyword

async def read_file_content(file_path: str) -> str:
    try:
        async with aiofiles.open(file_path, mode='r') as f:
            content = await f.read()
            logger.info("Read file %s with length %d", file_path, len(content))
            return content
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""

@measure_time
async def generate_rag_response(user_query: str, filter_by: str = None) -> str:
    """
    Generates a retrieval-augmented response for the given user query.
    
    If the query mentions a file name (e.g., "sessions.py", "README.md", etc.), 
    the full file content is retrieved (after case-insensitive matching) and used as context.
    For generic repository queries, FAISS retrieval is used and supplemented with key repository files.
    """
    try:
        repo_path = Path("cloned_repo")
        similarity_threshold = 0.5  # Adjust based on empirical evaluation.
        requested_k = 20  # Number of chunks to retrieve

        # Use a case-insensitive regex to detect any file name in the query.
        file_match = re.search(r'([A-Za-z0-9_.\-]+\.\w+)', user_query, re.IGNORECASE)
        if file_match:
            extracted_file = file_match.group(1).lower()
            # Normalize file names from the repository by lowercasing.
            matching_files = [f for f in repo_path.rglob("*") if f.is_file() and f.name.lower() == extracted_file]
            if matching_files:
                filter_by = extracted_file
                logger.info("Detected file name in query (case-insensitive): %s", filter_by)
            else:
                logger.info("File name %s detected in query but not found in repository.", extracted_file)

        context_chunks = []
        if filter_by:
            # For file-specific queries, retrieve full content.
            matching_files = [f for f in repo_path.rglob("*") if f.is_file() and f.name.lower() == filter_by.lower()]
            if matching_files:
                file_path = str(matching_files[0])
                full_content = await read_file_content(file_path)
                if full_content:
                    # Optionally, if the file is very long, summarize it.
                    if len(full_content.split()) > 1000:  # arbitrary threshold; adjust as needed
                        logger.info("File %s is long; summarizing its content.", file_path)
                        # Call a summarization function (you can implement this as needed).
                        full_content = await analyze_code("Please provide a summary of the following code.", full_content)
                    context_chunks = [f"**{file_path} (full file)**:\n{full_content}\n"]
                    logger.info("Using full content for file: %s", file_path)
                else:
                    logger.warning("Full content for %s is empty.", file_path)
            else:
                logger.warning("No matching file found for filter: %s", filter_by)
        else:
            # For generic repository queries, use FAISS retrieval.
            query_embedding = await generate_embedding(user_query)
            retrieval_results = query_faiss(query_embedding, k=requested_k)
            valid_chunks = []
            for idx, distance in zip(retrieval_results["indices"][0], retrieval_results["distances"][0]):
                if idx == -1 or distance < similarity_threshold:
                    continue
                if idx in metadata_store:
                    meta = metadata_store[idx]
                    file_chunk_id = meta["file_chunk_id"]
                    chunk_text = meta.get("chunk_text", "[No text available]")
                    valid_chunks.append(f"**{file_chunk_id}**:\n{chunk_text}\n")
            context_chunks.extend(valid_chunks)
            
            # Supplement with key repository files if context is insufficient.
            logger.info("Limited context from FAISS; adding key repository files.")
            key_files = ["README.md", "setup.py", "requirements.txt"]
            for key_file in key_files:
                matching = list(repo_path.rglob(key_file))
                if matching:
                    key_path = str(matching[0])
                    file_content = await read_file_content(key_path)
                    if file_content:
                        context_chunks.append(f"**{key_path} (full file)**:\n{file_content}\n")
        
        augmented_prompt = (
            "You are an expert code reviewer. Based on the following repository context, "
            "provide a comprehensive analysis covering the project's purpose, structure, dependencies, "
            "and notable features.\n\n"
            "Retrieved Context:\n" + "\n".join(context_chunks) + "\n\n"
            "Question: " + user_query + "\n\n"
            "If the context is limited, please synthesize a complete overview from the available information."
        )
        
        logger.info("Final augmented prompt sent to LLM:\n%s", augmented_prompt)
        
        async with AsyncRateLimiter(max_rate=10, time_period=1):
            response = await aclient.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer."},
                    {"role": "user", "content": augmented_prompt},
                ],
                temperature=0.2,
                max_tokens=600
            )
        
        final_response = response.choices[0].message.content.strip()
        logger.info("LLM response: %s", final_response)
        return final_response

    except Exception as e:
        logger.error("Error in generate_rag_response: %s", e)
        raise

if __name__ == '__main__':
    async def main():
        queries = [
            "What can you tell me about this full repository?",
            "What information can you provide me about the tests files in the repository?",
            "what can you tell me about the functions on sessions.py?"
        ]
        for q in queries:
            response = await generate_rag_response(q)
            print("Query:", q)
            print("Response:", response)
            print("-" * 60)
    asyncio.run(main())