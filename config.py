import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Flask Configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
DEBUG = FLASK_ENV == "development"
HOST = os.getenv("FLASK_HOST", "0.0.0.0")
PORT = int(os.getenv("FLASK_PORT", 5000))

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rag_system.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Vector Store Configuration
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIMENSION = 384  # For all-MiniLM-L6-v2

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.7))

# Text Processing Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))
MAX_CHUNKS_PER_URL = int(os.getenv("MAX_CHUNKS_PER_URL", 100))

# Queue Configuration
QUEUE_NAME = "url_ingestion_queue"
WORKER_TIMEOUT = int(os.getenv("WORKER_TIMEOUT", 300))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "./logs/app.log")

# Ensure directories exist
os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

