import faiss
import numpy as np
import os
import pickle
from sentence_transformers import SentenceTransformer
from config import FAISS_INDEX_PATH, EMBEDDING_MODEL, EMBEDDING_DIMENSION
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    """FAISS-based vector store for embeddings"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.index_path = FAISS_INDEX_PATH
        self.index = None
        self.id_map = {}  # Maps FAISS IDs to chunk metadata
        self.load_or_create_index()
    
    def load_or_create_index(self):
        """Load existing FAISS index or create a new one"""
        index_file = os.path.join(self.index_path, "index.faiss")
        id_map_file = os.path.join(self.index_path, "id_map.pkl")
        
        if os.path.exists(index_file) and os.path.exists(id_map_file):
            try:
                self.index = faiss.read_index(index_file)
                with open(id_map_file, 'rb') as f:
                    self.id_map = pickle.load(f)
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Error loading index: {e}. Creating new index.")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        self.index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
        self.id_map = {}
        logger.info("Created new FAISS index")
    
    def add_embeddings(self, texts, chunk_ids):
        """Add embeddings to the vector store
        
        Args:
            texts: List of text chunks
            chunk_ids: List of chunk IDs (database IDs)
        
        Returns:
            List of FAISS IDs
        """
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        embeddings = embeddings.astype('float32')
        
        faiss_ids = list(range(self.index.ntotal, self.index.ntotal + len(embeddings)))
        
        self.index.add(embeddings)
        
        for faiss_id, chunk_id in zip(faiss_ids, chunk_ids):
            self.id_map[faiss_id] = chunk_id
        
        self.save_index()
        logger.info(f"Added {len(texts)} embeddings to vector store")
        
        return faiss_ids
    
    def search(self, query, k=5):
        """Search for similar chunks
        
        Args:
            query: Query text
            k: Number of results to return
        
        Returns:
            List of (chunk_id, distance) tuples
        """
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True).astype('float32')
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx in self.id_map:
                results.append((self.id_map[idx], float(distance)))
        
        return results
    
    def save_index(self):
        """Save FAISS index to disk"""
        os.makedirs(self.index_path, exist_ok=True)
        index_file = os.path.join(self.index_path, "index.faiss")
        id_map_file = os.path.join(self.index_path, "id_map.pkl")
        
        faiss.write_index(self.index, index_file)
        with open(id_map_file, 'wb') as f:
            pickle.dump(self.id_map, f)
        
        logger.info(f"Saved FAISS index to {index_file}")
    
    def get_index_stats(self):
        """Get statistics about the index"""
        return {
            "total_vectors": self.index.ntotal,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "model": EMBEDDING_MODEL
        }

# Global vector store instance
_vector_store = None

def get_vector_store():
    """Get or create the global vector store instance"""
    # global _vector_store
    # if _vector_store is None:
    #     _vector_store = VectorStore()
    return VectorStore()

