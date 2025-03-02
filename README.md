# Repository-Analysis-with-OpenAI-APIs

## Overview:
Repository Analysis with OpenAI APIs is an asynchronous Python application that clones Git repositories,
processes their code files into embeddings, and uses OpenAI's API to provide intelligent code analysis.
The application leverages a FAISS vector store to efficiently search for and retrieve relevant code snippets,
and it uses a retrieval-augmented generation (RAG) approach to answer queries about the repository or
specific files.

## Installation Guide:
### Prerequisites:
    - Python 3.11 or later
    - Git (installed locally or available in your Docker image)
    - Docker (optional, for containerized deployment)

### Setup Instructions:
1. **Clone the Repository**:
```
    git clone https://github.com/dor851997/Repository-Analysis-with-OpenAI-APIs.git
    cd Repository-Analysis-with-OpenAI-APIs
```
2. Create and Activate a Virtual Environment:
```
       python3 -m venv venv
       source venv/bin/activate
```
3. Install Dependencies:
```
       pip install --upgrade pip
       pip install -r requirements.txt
```

4. Configure Environment Variables:

   Create a .env file in the project root with your OpenAI API key:
```
       OPENAI_API_KEY=your_openai_api_key_here
       FAISS_INDEX_FILE=faiss_index.idx
       FAISS_METADATA_FILE=faiss_metadata.json
```

6. (Optional) Docker Setup:
   - Build the Docker Image:
         ```docker build -t repo-analysis .```
   - Run the Container:
         ```docker run -p 8000:8000 repo-analysis```

## Usage Examples:
1. Running the Application Locally:
    ```
    uvicorn src.api.endpoints:app --reload
    ```
   The API will be available at [http://127.0.0.1:8000/docs#/](http://127.0.0.1:8000/docs#/)

2. API Endpoints:
   - Clone Repository:

         Endpoint: /clone (POST)
         Payload: {"repo_url": "https://github.com/psf/requests"}
         Description: Clones the specified GitHub repository and processes its files to generate embeddings.

   - Analyze Repository / Specific File:

         Endpoint: /analyse_repository (POST)
         Payload Examples:
           Generic Query:
             {"query": "What can you tell me about the repository?"}
           File-Specific Query:
             {"query": "What can you tell me about the functions on sessions.py?"}
         Description: Uses a retrieval-augmented generation (RAG) approach. If a file name (e.g., sessions.py)
                      is mentioned, the full content of that file is used as context; otherwise, relevant context
                      is retrieved via FAISS and supplemented with key repository files (like README.txt, setup.py).

## Design Decisions:
- Asynchronous Architecture:
  Uses async/await to efficiently handle I/O-bound tasks such as repository cloning, file processing,
  and API calls.

- FAISS for Vector Storage:
  Splits repository files into chunks and converts them into embeddings via OpenAI's API.
  Embeddings are stored in a FAISS index along with metadata for fast similarity searches.

- Retrieval-Augmented Generation (RAG):
  Constructs a detailed prompt by combining context from full file content (when a file is mentioned)
  or from FAISS-retrieved chunks (supplemented with key files) to generate a comprehensive analysis.

- Modular Code Organization:
  The project is split into several core modules:
    * Repository Management (repository.py)
    * Vectorstore (vectorstore.py)
    * Assistant Integration (assistant.py)
    * API Endpoints (endpoints.py)
    * Utilities (rate_limiter.py and performance.py)

## Performance Considerations:
- Rate Limiting:
  An asynchronous rate limiter controls API calls to OpenAI, ensuring compliance with rate limits.

- Performance Monitoring:
  Middleware logs request durations and memory usage, helping to monitor and optimize performance.

- Efficient File Processing:
  Files are effectively chunked, with options for overlapping or semantic chunking to improve context retrieval.

- FAISS Retrieval Tuning:
  Parameters such as similarity thresholds and the number of retrieved chunks are tuned to ensure
  sufficient context for the LLM to generate detailed responses.

## Future Improvements:
- Advanced Chunking Strategies:
  Implement overlapping or semantically aware chunking to improve the quality of context retrieval.

- Caching and Incremental Updates:
  Cache cloned repositories or update them incrementally to reduce processing time on subsequent requests.

- Enhanced Telemetry:
  Integrate with performance monitoring tools (e.g., Prometheus, Grafana) for real-time tracking of metrics.

- CLI Interface:
  Develop a command-line interface to facilitate local testing and usage.

- Container Orchestration Enhancements:
  Expand the Docker setup to support multi-container deployments and automated scaling.

## License:
This project is licensed under the MIT License. See the LICENSE file for details.
