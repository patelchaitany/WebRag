from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import json
import logging
from datetime import datetime
from pydantic import BaseModel, ValidationError
from models import init_db, SessionLocal, URLMetadata, ChunkMetadata, IngestionStatus
from vector_store import get_vector_store
from llm_provider import generate_answer
from config import (
    FLASK_ENV, DEBUG, HOST, PORT, REDIS_URL, QUEUE_NAME,
    LLM_MODEL, LOG_LEVEL, LOG_FILE
)
import os

# Setup logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize database
init_db()

# Redis client
redis_client = redis.from_url(REDIS_URL)

# Pydantic models for validation
class IngestURLRequest(BaseModel):
    url: str

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.route('/ingest-url', methods=['POST'])
def ingest_url():
    """
    Ingest a URL for RAG processing

    Request body:
    {
        "url": "https://example.com"
    }

    Response: 202 Accepted
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        ingest_request = IngestURLRequest(**data)
        url = ingest_request.url

        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return jsonify({"error": "Invalid URL format"}), 400

        db = SessionLocal()
        try:
            # Check if URL already exists
            existing = db.query(URLMetadata).filter(URLMetadata.url == url).first()

            if existing:
                if existing.status == IngestionStatus.COMPLETED:
                    return jsonify({
                        "message": "URL already ingested",
                        "url": url,
                        "status": existing.status.value,
                        "chunk_count": existing.chunk_count
                    }), 200
                elif existing.status == IngestionStatus.PROCESSING:
                    return jsonify({
                        "message": "URL is currently being processed",
                        "url": url,
                        "status": existing.status.value
                    }), 202
                elif existing.status == IngestionStatus.FAILED:
                    # Retry failed ingestion
                    existing.status = IngestionStatus.PENDING
                    existing.error_message = None
                    db.commit()
            else:
                # Create new URL metadata
                url_metadata = URLMetadata(url=url, status=IngestionStatus.PENDING)
                db.add(url_metadata)
                db.commit()

            # Push job to Redis queue
            job = {"url": url, "timestamp": datetime.utcnow().isoformat()}
            redis_client.rpush(QUEUE_NAME, json.dumps(job))

            logger.info(f"URL ingestion job queued: {url}")

            return jsonify({
                "message": "URL ingestion job accepted",
                "url": url,
                "status": "pending"
            }), 202

        finally:
            db.close()

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": "Invalid request format"}), 400
    except Exception as e:
        logger.error(f"Error in ingest_url: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/query', methods=['POST'])
def query_rag():
    """
    Query the RAG system

    Request body:
    {
        "query": "What is the main topic?",
        "top_k": 5
    }

    Response: Answer with source chunks
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        query_request = QueryRequest(**data)
        query = query_request.query
        top_k = query_request.top_k

        if not query or len(query.strip()) == 0:
            return jsonify({"error": "Query cannot be empty"}), 400

        if top_k < 1 or top_k > 20:
            return jsonify({"error": "top_k must be between 1 and 20"}), 400

        # Search vector store
        vector_store = get_vector_store()
        search_results = vector_store.search(query, k=top_k)

        if not search_results:
            return jsonify({
                "query": query,
                "answer": "No relevant content found in the ingested documents.",
                "sources": []
            }), 200

        # Retrieve chunk content from database
        db = SessionLocal()
        try:
            chunk_ids = [chunk_id for chunk_id, _ in search_results]
            chunks = db.query(ChunkMetadata).filter(ChunkMetadata.id.in_(chunk_ids)).all()

            chunk_map = {chunk.id: chunk for chunk in chunks}
            source_chunks = []

            for chunk_id, distance in search_results:
                if chunk_id in chunk_map:
                    chunk = chunk_map[chunk_id]
                    source_chunks.append({
                        "content": chunk.content[:500],
                        "distance": distance,
                        "chunk_index": chunk.chunk_index
                    })

            # Generate answer using LLM
            context = "\n\n".join([chunk["content"] for chunk in source_chunks])
            answer = generate_answer(query, context)

            logger.info(f"Query processed: {query}")

            return jsonify({
                "query": query,
                "answer": answer,
                "sources": source_chunks,
                "model": LLM_MODEL
            }), 200

        finally:
            db.close()

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"error": "Invalid request format"}), 400
    except Exception as e:
        logger.error(f"Error in query_rag: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info(f"Starting Flask app in {FLASK_ENV} mode")
    app.run(host=HOST, port=PORT, debug=DEBUG)

