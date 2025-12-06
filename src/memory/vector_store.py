"""
Vector Store for semantic search using ChromaDB
"""
import os
import logging
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector embeddings and semantic search"""
    
    def __init__(self):
        self.chromadb_host = os.getenv('CHROMADB_HOST', 'localhost')
        self.chromadb_port = int(os.getenv('CHROMADB_PORT', 8000))
        self.client = None
        self.collection = None
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    async def initialize(self):
        """Initialize ChromaDB connection"""
        try:
            self.client = chromadb.HttpClient(
                host=self.chromadb_host,
                port=self.chromadb_port
            )
            self.collection = self.client.get_or_create_collection(
                name="conversations",
                metadata={"description": "Conversation history embeddings"}
            )
            logger.info("Vector store initialized")
        except Exception as e:
            logger.error(f"Vector store initialization failed: {e}")
            raise
    
    async def add_conversation(
        self,
        conversation_id: str,
        text: str,
        metadata: Dict[str, Any]
    ):
        """Add conversation to vector store"""
        try:
            logger.info(f"Adding conversation {conversation_id} to vector store")
            embedding = self.embedding_model.encode(text).tolist()
            self.collection.add(
                ids=[conversation_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[text]
            )
            logger.info(f"Successfully added conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error adding to vector store: {e}")
            raise
    
    async def search_similar(
        self,
        query: str,
        max_results: int = 5,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar conversations"""
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                where=filter_metadata
            )
            
            formatted_results = []
            if results['ids']:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': doc_id,
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i]
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if vector store is healthy"""
        try:
            self.client.heartbeat()
            return True
        except:
            return False
