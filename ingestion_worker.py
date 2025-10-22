import json
import logging
import redis
from datetime import datetime
from requests import get as requests_get
import html2text
from sqlalchemy.orm import Session
from models import URLMetadata, ChunkMetadata, IngestionStatus, SessionLocal
from vector_store import get_vector_store
from config import REDIS_URL, QUEUE_NAME, CHUNK_SIZE, CHUNK_OVERLAP, MAX_CHUNKS_PER_URL
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class URLIngestionWorker:
    """Worker for processing URL ingestion jobs from Redis queue"""
    
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL)
        self.vector_store = get_vector_store()
        self.db = SessionLocal()
    
    def fetch_and_clean_content(self, url):
        """Fetch URL content and clean it using html2text

        Args:
            url: URL to fetch

        Returns:
            Tuple of (title, cleaned_text)
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests_get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Configure html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.ignore_emphasis = False
            h.body_width = 0  # Don't wrap text
            h.unicode_snob = True

            # Convert HTML to text
            text = h.handle(response.text)

            # Extract title from URL or response
            title = url.split('/')[-1] or url

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            logger.info(f"Successfully fetched and converted {url} to text ({len(text)} characters)")

            return title, text

        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            raise
    
    def chunk_text(self, text):
        """Split text into overlapping chunks
        
        Args:
            text: Text to chunk
        
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - CHUNK_OVERLAP
        
        return chunks[:MAX_CHUNKS_PER_URL]
    
    def process_url(self, url):
        """Process a single URL

        Args:
            url: URL to process
        """
        url_metadata = self.db.query(URLMetadata).filter(URLMetadata.url == url).first()

        if not url_metadata:
            logger.error(f"URL metadata not found for {url}")
            return

        try:
            # Update status to processing
            url_metadata.status = IngestionStatus.PROCESSING
            self.db.commit()
            logger.info(f"Processing URL: {url}")

            # Delete existing chunks for this URL (if retrying)
            existing_chunks = self.db.query(ChunkMetadata).filter(ChunkMetadata.url_id == url_metadata.id).all()
            if existing_chunks:
                logger.info(f"Deleting {len(existing_chunks)} existing chunks for URL: {url}")
                for chunk in existing_chunks:
                    self.db.delete(chunk)
                self.db.commit()

            # Fetch and clean content
            title, content = self.fetch_and_clean_content(url)
            url_metadata.title = title
            url_metadata.content_length = len(content)

            # Chunk text
            chunks = self.chunk_text(content)

            if not chunks:
                raise ValueError("No content chunks generated")

            # Create chunk metadata and get embeddings
            chunk_ids = []
            chunk_texts = []

            for idx, chunk in enumerate(chunks):
                chunk_meta = ChunkMetadata(
                    url_id=url_metadata.id,
                    chunk_index=idx,
                    content=chunk,
                    faiss_id=None  # Will be updated after embedding
                )
                self.db.add(chunk_meta)
                self.db.flush()
                chunk_ids.append(chunk_meta.id)
                chunk_texts.append(chunk)

            # Add embeddings to vector store
            faiss_ids = self.vector_store.add_embeddings(chunk_texts, chunk_ids)

            # Update chunk metadata with FAISS IDs
            for chunk_meta, faiss_id in zip(
                self.db.query(ChunkMetadata).filter(ChunkMetadata.id.in_(chunk_ids)).all(),
                faiss_ids
            ):
                chunk_meta.faiss_id = faiss_id

            # Update URL metadata
            url_metadata.chunk_count = len(chunks)
            url_metadata.status = IngestionStatus.COMPLETED
            url_metadata.completed_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"Successfully processed URL: {url} with {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            url_metadata.status = IngestionStatus.FAILED
            url_metadata.error_message = str(e)
            self.db.commit()
    
    def run(self):
        """Main worker loop"""
        logger.info("Starting URL ingestion worker...")
        
        while True:
            try:
                # Get job from queue
                job = self.redis_client.blpop(QUEUE_NAME, timeout=5)
                
                if job:
                    _, job_data = job
                    job_dict = json.loads(job_data)
                    url = job_dict.get('url')
                    
                    if url:
                        self.process_url(url)
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                time.sleep(1)

def start_worker():
    """Start the ingestion worker"""
    worker = URLIngestionWorker()
    worker.run()

if __name__ == "__main__":
    start_worker()

