import hashlib
import logging
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_url_hash(url):
    """Generate a hash for a URL
    
    Args:
        url: URL string
    
    Returns:
        SHA256 hash of the URL
    """
    return hashlib.sha256(url.encode()).hexdigest()

def validate_url(url):
    """Validate URL format
    
    Args:
        url: URL string
    
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False

def truncate_text(text, max_length=500):
    """Truncate text to max length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def format_timestamp(dt):
    """Format datetime to ISO format
    
    Args:
        dt: Datetime object
    
    Returns:
        ISO formatted string
    """
    if dt is None:
        return None
    return dt.isoformat()

def get_current_timestamp():
    """Get current timestamp in ISO format
    
    Returns:
        Current timestamp
    """
    return datetime.utcnow().isoformat()

def calculate_similarity_score(distance):
    """Convert FAISS distance to similarity score (0-1)
    
    Args:
        distance: FAISS L2 distance
    
    Returns:
        Similarity score between 0 and 1
    """
    # L2 distance to similarity: similarity = 1 / (1 + distance)
    return 1 / (1 + distance)

def batch_list(items, batch_size):
    """Batch a list into smaller lists
    
    Args:
        items: List to batch
        batch_size: Size of each batch
    
    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

