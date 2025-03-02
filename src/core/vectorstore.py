from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import os
import json
from typing import List, Dict, Any
import numpy as np
import faiss
import concurrent.futures
import openai
from openai import AsyncOpenAI
import time
import functools

from src.utils.performance import measure_time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

DIMENSION = 1536  # Embedding dimension
FAISS_INDEX_FILE = os.environ.get("FAISS_INDEX_FILE", "faiss_index.idx")
METADATA_FILE = os.environ.get("FAISS_METADATA_FILE", "faiss_metadata.json")

if os.path.exists(FAISS_INDEX_FILE):
    faiss_index = faiss.read_index(FAISS_INDEX_FILE)
    logger.info(f"Loaded FAISS index from {FAISS_INDEX_FILE}.")
else:
    faiss_index = faiss.IndexFlatL2(DIMENSION)
    logger.info("Created new FAISS index.")

if os.path.exists(METADATA_FILE):
    try:
        with open(METADATA_FILE, "r") as f:
            meta_data = json.load(f)
        metadata_store = {int(k): v for k, v in meta_data.get("metadata_store", {}).items()}
        global_id_counter = meta_data.get("global_id_counter", 0)
        logger.info(f"Loaded metadata from {METADATA_FILE} with global_id_counter {global_id_counter}.")
    except Exception as e:
        logger.error(f"Error loading metadata: {e}")
        metadata_store = {}
        global_id_counter = 0
else:
    metadata_store: Dict[int, Dict[str, Any]] = {}
    global_id_counter = 0

aclient = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def save_metadata():
    try:
        with open(METADATA_FILE, "w") as f:
            json.dump({
                "global_id_counter": global_id_counter,
                "metadata_store": {str(k): v for k, v in metadata_store.items()}
            }, f, indent=2)
        logger.info(f"Metadata saved to {METADATA_FILE}.")
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")

def chunk_text(text: str, chunk_size: int = 2000) -> List[str]:
    try:
        if not isinstance(text, str):
            raise ValueError("Expected text to be a string.")
        chunks = [text[i: i + chunk_size] for i in range(0, len(text), chunk_size)]
        logger.debug(f"Generated {len(chunks)} chunks from text of length {len(text)}.")
        return chunks
    except Exception as e:
        logger.error(f"Error chunking text: {e}")
        return []

@measure_time
async def generate_embedding(text: str) -> List[float]:
    try:
        response = await aclient.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding of length {len(embedding)} for text of length {len(text)}.")
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise

@measure_time
async def store_embeddings(embeddings: Dict[str, Any], chunk_texts: Dict[str, str]) -> None:
    global global_id_counter, faiss_index, metadata_store
    try:
        new_vectors = []
        new_metadata = {}
        for file_chunk_id, vector in embeddings.items():
            np_vector = np.array(vector, dtype=np.float32)
            if np_vector.shape[0] != DIMENSION:
                logger.error(f"Embedding dimension mismatch for {file_chunk_id}. Expected {DIMENSION}, got {np_vector.shape[0]}")
                continue
            new_vectors.append(np_vector)
            new_metadata[global_id_counter] = {
                "file_chunk_id": file_chunk_id,
                "chunk_text": chunk_texts[file_chunk_id]
            }
            global_id_counter += 1

        if new_vectors:
            vectors_np = np.vstack(new_vectors)
            loop = asyncio.get_running_loop()
            def add_vectors():
                faiss_index.add(vectors_np)
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await loop.run_in_executor(pool, add_vectors)
            metadata_store.update(new_metadata)
            logger.info(f"Stored {len(new_vectors)} embeddings in FAISS index.")
            faiss.write_index(faiss_index, FAISS_INDEX_FILE)
            logger.info(f"FAISS index saved to {FAISS_INDEX_FILE}.")
            save_metadata()
        else:
            logger.warning("No new vectors to store.")
    except Exception as e:
        logger.error(f"Error storing embeddings in FAISS: {e}")
        raise

@measure_time
async def process_code_file(file_path: str, content: str) -> None:
    try:
        chunks = chunk_text(content)
        if not chunks:
            logger.warning(f"No chunks generated for file: {file_path}")
        embeddings = {}
        chunk_texts = {}
        for i, chunk in enumerate(chunks):
            try:
                embedding = await generate_embedding(chunk)
                key = f"{file_path}_chunk_{i}"
                embeddings[key] = embedding
                chunk_texts[key] = chunk
            except Exception as inner_e:
                logger.error(f"Error processing chunk {i} in file {file_path}: {inner_e}")
        if embeddings:
            await store_embeddings(embeddings, chunk_texts)
        else:
            logger.warning(f"No embeddings were generated for file: {file_path}")
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        raise

def query_faiss(query_vector: List[float], k: int = 1) -> Dict[str, Any]:
    np_query = np.array(query_vector, dtype=np.float32).reshape(1, -1)
    distances, indices = faiss_index.search(np_query, k)
    return {"distances": distances, "indices": indices}

