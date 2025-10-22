# 🚀 RAG API System - Retrieval-Augmented Generation

A production-ready **Retrieval-Augmented Generation (RAG)** API system that ingests URLs asynchronously and provides intelligent query responses grounded in the ingested content.

**Status:** ✅ Production Ready | **Version:** 1.1.0

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Technology Stack](#technology-stack)
3. [Database Schema](#database-schema)
4. [API Documentation](#api-documentation)
5. [Setup Instructions](#setup-instructions)
6. [Environment Variables](#environment-variables)
7. [Docker Deployment](#docker-deployment)
8. [Testing the API](#testing-the-api)
9. [Troubleshooting](#troubleshooting)

---

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATION                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
   ┌─────────────┐              ┌──────────────┐
   │ POST /ingest│              │ POST /query  │
   │    -url     │              │              │
   └──────┬──────┘              └──────┬───────┘
          │                            │
          ▼                            ▼
   ┌──────────────────────────────────────────┐
   │         FLASK REST API SERVER            │
   │  (app.py - Request Validation & Routing) │
   └──────┬───────────────────────────┬───────┘
          │                           │
          ▼                           ▼
   ┌─────────────────┐        ┌──────────────────┐
   │  REDIS QUEUE    │        │  VECTOR STORE    │
   │  (Job Queue)    │        │  (FAISS Index)   │
   └────────┬────────┘        └────────┬─────────┘
            │                          │
            ▼                          ▼
   ┌──────────────────────┐   ┌──────────────────┐
   │ INGESTION WORKER     │   │  SIMILARITY      │
   │ (ingestion_worker.py)│   │  SEARCH          │
   │                      │   │                  │
   │ 1. Fetch URL         │   │ 1. Embed Query   │
   │ 2. Convert HTML→Text │   │ 2. Search FAISS  │
   │ 3. Chunk Text        │   │ 3. Retrieve Top-K│
   │ 4. Generate Embeddings   │                  │
   │ 5. Store in FAISS    │   └────────┬─────────┘
   │ 6. Store Metadata    │            │
   └──────┬───────────────┘            ▼
          │                   ┌──────────────────┐
          │                   │  LLM PROVIDER    │
          │                   │ (litellm)        │
          │                   │                  │
          │                   │ Generate Answer  │
          │                   │ with Context     │
          │                   └────────┬─────────┘
          │                            │
          ▼                            ▼
   ┌──────────────────────────────────────────┐
   │      SQLITE DATABASE                     │
   │  ┌──────────────────────────────────┐   │
   │  │ url_metadata                     │   │
   │  │ - URL, Status, Chunks, Metadata  │   │
   │  └──────────────────────────────────┘   │
   │  ┌──────────────────────────────────┐   │
   │  │ chunk_metadata                   │   │
   │  │ - Content, FAISS ID, Chunk Index │   │
   │  └──────────────────────────────────┘   │
   └──────────────────────────────────────────┘
```

### Data Flow

#### **Ingestion Flow (Asynchronous)**
```
1. Client sends URL → /ingest-url endpoint
2. API validates URL and creates URLMetadata record
3. Job pushed to Redis queue (202 Accepted response)
4. Worker picks up job from queue
5. Worker fetches URL content
6. HTML converted to clean text (html2text)
7. Text split into overlapping chunks
8. Embeddings generated (Sentence Transformers)
9. Embeddings stored in FAISS index
10. Metadata stored in SQLite
11. Status updated to COMPLETED
```

#### **Query Flow (Synchronous)**
```
1. Client sends query → /query endpoint
2. Query embedded using same model
3. FAISS performs similarity search
4. Top-K chunks retrieved from database
5. Context assembled from chunks
6. LLM generates answer using context
7. Response returned with sources
```

---

## 🛠️ Technology Stack - Why These Technologies?

| Technology | Purpose | Why Chosen |
|-----------|---------|-----------|
| **Flask** | REST API Framework | Lightweight, easy to understand, perfect for microservices |
| **Redis** | Message Queue | Fast, reliable job queue for async processing |
| **FAISS** | Vector Database | Facebook's efficient similarity search, handles millions of vectors |
| **SQLite** | Metadata Storage | Lightweight, no server needed, perfect for development/small deployments |
| **SQLAlchemy** | ORM | Type-safe database operations, easy migrations |
| **Sentence Transformers** | Text Embeddings | Pre-trained, efficient, 384-dim embeddings for semantic search |
| **LiteLLM** | LLM Interface | Unified API for multiple LLM providers (OpenAI, Anthropic, Groq, etc.) |
| **html2text** | HTML Parsing | Converts HTML to clean Markdown/text, preserves structure |
| **Pydantic** | Data Validation | Type hints, automatic validation, clear error messages |
| **CORS** | Cross-Origin Support | Enables API access from web browsers |

### Architecture Justifications

#### **Asynchronous Processing**
- ✅ URLs can take 5-30 seconds to fetch and process
- ✅ Redis queue prevents blocking the API
- ✅ Clients get immediate 202 response
- ✅ Worker processes jobs in background

#### **Vector Store (FAISS)**
- ✅ Efficient similarity search (O(log n) with indexing)
- ✅ Handles large-scale embeddings
- ✅ Persistent storage on disk
- ✅ No external service needed

#### **SQLite for Metadata**
- ✅ No database server setup required
- ✅ Perfect for development and small deployments
- ✅ Easy to backup and migrate
- ✅ Scales to millions of records

#### **Sentence Transformers**
- ✅ Pre-trained on semantic similarity
- ✅ 384-dimensional embeddings (good balance of size/quality)
- ✅ Fast inference (~1ms per sentence)
- ✅ No API calls needed (runs locally)

---

## 📊 Database Schema

### Table: `url_metadata`

Stores information about ingested URLs and their processing status.

```sql
CREATE TABLE url_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url VARCHAR(2048) UNIQUE NOT NULL,
    title VARCHAR(512),
    status ENUM('pending', 'processing', 'completed', 'failed'),
    content_length INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);
```

**Fields:**
- `id`: Unique identifier
- `url`: The ingested URL (unique constraint)
- `title`: Extracted page title
- `status`: Current processing status
- `content_length`: Total characters in content
- `chunk_count`: Number of text chunks created
- `error_message`: Error details if status is FAILED
- `created_at`: When URL was first ingested
- `updated_at`: Last update timestamp
- `completed_at`: When processing finished

**Indexes:** `url`, `status`, `created_at`

---

### Table: `chunk_metadata`

Stores individual text chunks and their embeddings.

```sql
CREATE TABLE chunk_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    faiss_id INTEGER UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (url_id) REFERENCES url_metadata(id)
);
```

**Fields:**
- `id`: Unique chunk identifier
- `url_id`: Foreign key to url_metadata
- `chunk_index`: Position in the document (0-based)
- `content`: The actual text chunk (up to 500 chars)
- `faiss_id`: Index in FAISS vector store (nullable until embedding)
- `created_at`: When chunk was created

**Indexes:** `url_id`, `faiss_id`

---

### Vector Store (FAISS)

**Location:** `./data/faiss_index/`

**Files:**
- `index.faiss`: Binary FAISS index file
- `id_map.pkl`: Python pickle mapping FAISS IDs to chunk IDs

**Configuration:**
- **Index Type:** IndexFlatL2 (L2 distance metric)
- **Dimension:** 384 (from Sentence Transformers)
- **Distance Metric:** Euclidean (L2)

**Why L2 Distance?**
- Standard metric for semantic similarity
- Works well with normalized embeddings
- Efficient computation

---

## 📡 API Documentation

### Endpoint 1: POST `/ingest-url`

**Purpose:** Queue a URL for asynchronous ingestion

**Request:**
```json
{
    "url": "https://example.com/article"
}
```

**Response (202 Accepted):**
```json
{
    "message": "URL ingestion job accepted",
    "url": "https://example.com/article",
    "status": "pending"
}
```

**Response (200 - Already Ingested):**
```json
{
    "message": "URL already ingested",
    "url": "https://example.com/article",
    "status": "completed",
    "chunk_count": 15
}
```

**Response (202 - Processing):**
```json
{
    "message": "URL is currently being processed",
    "url": "https://example.com/article",
    "status": "processing"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid URL format or missing body
- `500 Internal Server Error`: Server error

**cURL Example:**
```bash
curl -X POST http://localhost:5000/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://codeforces.com/contest/2154/problem/C"}'
```

---

### Endpoint 2: POST `/query`

**Purpose:** Query the ingested content and get AI-generated answers

**Request:**
```json
{
    "query": "What is the main topic?",
    "top_k": 5
}
```

**Parameters:**
- `query` (string, required): The question to ask
- `top_k` (integer, optional): Number of chunks to retrieve (1-20, default: 5)

**Response (200 OK):**
```json
{
    "query": "What is the main topic?",
    "answer": "The main topic is about competitive programming...",
    "sources": [
        {
            "content": "This is a competitive programming problem about...",
            "distance": 0.234,
            "chunk_index": 0
        },
        {
            "content": "The problem requires understanding of algorithms...",
            "distance": 0.456,
            "chunk_index": 2
        }
    ],
    "model": "groq/llama-3.3-70b-versatile"
}
```

**Response (200 - No Content):**
```json
{
    "query": "What is the main topic?",
    "answer": "No relevant content found in the ingested documents.",
    "sources": []
}
```

**Error Responses:**
- `400 Bad Request`: Invalid query or top_k out of range
- `500 Internal Server Error`: Server error

**cURL Example:**
```bash
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this problem about?",
    "top_k": 5
  }'
```

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8+
- Redis server
- 2GB RAM (for embeddings model)
- Internet connection (for downloading models)

### Step 1: Clone and Navigate

```bash
cd /home/phinex/hack/AiAR
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your settings (see [Environment Variables](#environment-variables) section)

### Step 5: Initialize Database

```bash
python -c "from models import init_db; init_db()"
```

### Step 6: Start Redis

```bash
# On macOS/Linux
redis-server

# On Windows (if installed via WSL or native)
redis-server
```

### Step 7: Start the API Server

```bash
# Terminal 1
python app.py
```

Output:
```
 * Running on http://0.0.0.0:5000
 * Press CTRL+C to quit
```

### Step 8: Start the Ingestion Worker

```bash
# Terminal 2
python ingestion_worker.py
```

Output:
```
INFO:__main__:Starting URL ingestion worker...
```

---

## 🔧 Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Flask Configuration
FLASK_ENV=development
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
DEBUG=True

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database Configuration
DATABASE_URL=sqlite:///./rag_system.db

# Vector Store Configuration
FAISS_INDEX_PATH=./data/faiss_index
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# LLM Configuration
LLM_MODEL=groq/llama-3.3-70b-versatile
LLM_API_KEY=your-api-key-here
LLM_TEMPERATURE=0.7

# Text Processing Configuration
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_CHUNKS_PER_URL=100

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### Configuration Details

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | development | Flask environment (development/production) |
| `FLASK_PORT` | 5000 | Port to run API server |
| `FLASK_HOST` | 0.0.0.0 | Host to bind to |
| `DEBUG` | True | Enable Flask debug mode |
| `REDIS_HOST` | localhost | Redis server host |
| `REDIS_PORT` | 6379 | Redis server port |
| `REDIS_DB` | 0 | Redis database number |
| `DATABASE_URL` | sqlite:///./rag_system.db | SQLite database path |
| `FAISS_INDEX_PATH` | ./data/faiss_index | FAISS index directory |
| `EMBEDDING_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | Embedding model |
| `LLM_MODEL` | groq/llama-3.3-70b-versatile | LLM model to use |
| `LLM_API_KEY` | (required) | API key for LLM provider |
| `LLM_TEMPERATURE` | 0.7 | LLM temperature (0-1) |
| `CHUNK_SIZE` | 500 | Characters per chunk |
| `CHUNK_OVERLAP` | 50 | Overlap between chunks |
| `MAX_CHUNKS_PER_URL` | 100 | Max chunks per URL |
| `LOG_LEVEL` | INFO | Logging level |
| `LOG_FILE` | ./logs/app.log | Log file path |

### Supported LLM Providers

LiteLLM supports multiple providers. Set `LLM_MODEL` to:

- **OpenAI:** `gpt-3.5-turbo`, `gpt-4`
- **Anthropic:** `claude-3-opus-20240229`, `claude-3-sonnet-20240229`
- **Groq:** `groq/llama-3.3-70b-versatile`, `groq/mixtral-8x7b-32768`
- **Cohere:** `command-r-plus`
- **Ollama (local):** `ollama/llama2`

---

## 🐳 Docker Deployment

### Using Docker Compose

```bash
docker-compose up -d
```

This starts:
- Flask API on port 5000
- Redis on port 6379
- Ingestion worker

### Manual Docker Build

```bash
# Build image
docker build -t rag-api:latest .

# Run API
docker run -p 5000:5000 \
  -e REDIS_HOST=redis \
  -e LLM_API_KEY=your-key \
  rag-api:latest python app.py

# Run worker
docker run \
  -e REDIS_HOST=redis \
  -e LLM_API_KEY=your-key \
  rag-api:latest python ingestion_worker.py
```

---

## 🧪 Testing the API

### Test 1: Ingest a URL

```bash
curl -X POST http://localhost:5000/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"}'
```

Expected response:
```json
{
    "message": "URL ingestion job accepted",
    "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "status": "pending"
}
```

### Test 2: Wait for Processing

Wait 5-10 seconds for the worker to process the URL.

Check logs:
```bash
tail -f ./logs/app.log
```

### Test 3: Query the Content

```bash
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is artificial intelligence?",
    "top_k": 3
  }'
```

Expected response:
```json
{
    "query": "What is artificial intelligence?",
    "answer": "Artificial intelligence (AI) is the simulation of human intelligence...",
    "sources": [
        {
            "content": "Artificial intelligence (AI) is intelligence demonstrated by machines...",
            "distance": 0.123,
            "chunk_index": 0
        }
    ],
    "model": "groq/llama-3.3-70b-versatile"
}
```

### Test 4: Re-ingest Same URL

```bash
curl -X POST http://localhost:5000/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"}'
```

Expected response (should return 200 with existing data):
```json
{
    "message": "URL already ingested",
    "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "status": "completed",
    "chunk_count": 42
}
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused" on Redis

**Solution:**
```bash
# Start Redis
redis-server

# Or check if Redis is running
redis-cli ping  # Should return PONG
```

### Issue: "UNIQUE constraint failed: chunk_metadata.faiss_id"

**Solution:**
```bash
# Run the database migration script
python fix_database.py

# Restart the worker
python ingestion_worker.py
```

See `UNIQUE_CONSTRAINT_FIX.md` for detailed explanation.

### Issue: "No module named 'torch'"

**Solution:**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Issue: Worker not processing URLs

**Check:**
1. Redis is running: `redis-cli ping`
2. Worker is running: Check terminal output
3. Check logs: `tail -f ./logs/app.log`
4. Check Redis queue: `redis-cli LLEN url_ingestion_queue`

### Issue: Slow query responses

**Optimization:**
1. Reduce `top_k` parameter
2. Increase `CHUNK_SIZE` to reduce number of chunks
3. Use GPU-accelerated FAISS (install `faiss-gpu`)
4. Use a faster LLM model

### Issue: Out of memory

**Solution:**
1. Reduce `MAX_CHUNKS_PER_URL`
2. Reduce `CHUNK_SIZE`
3. Use a smaller embedding model
4. Deploy on a machine with more RAM

---

## 📁 Project Structure

```
AiAR/
├── app.py                      # Flask API server
├── ingestion_worker.py         # Background worker
├── models.py                   # SQLAlchemy models
├── config.py                   # Configuration
├── vector_store.py             # FAISS wrapper
├── llm_provider.py             # LLM integration
├── prompts.py                  # System prompts
├── fix_database.py             # Database migration
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment file
├── Dockerfile                  # Docker image
├── docker-compose.yml          # Docker Compose config
├── README.md                   # This file
├── data/
│   └── faiss_index/            # FAISS index files
├── logs/
│   └── app.log                 # Application logs
└── rag_system.db               # SQLite database
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📞 Support

For issues and questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs in `./logs/app.log`
3. Check `UNIQUE_CONSTRAINT_FIX.md` for known issues
4. Open an issue on GitHub

---

**Last Updated:** 2024-01-15
**Version:** 1.1.0
**Status:** ✅ Production Ready
