"""
Hybrid Search combining keyword (BM25) and semantic search for better retrieval.
"""
import logging
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class BM25Searcher:
    """Simple in-memory BM25 implementation for keyword search."""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, str] = {}
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length = 0.0
        self.total_docs = 0
        
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        return text.lower().split()
    
    def add_document(self, doc_id: str, text: str):
        """Add a document to the index."""
        tokens = self._tokenize(text)
        self.documents[doc_id] = text
        self.doc_lengths[doc_id] = len(tokens)
        
        # Update document frequencies
        unique_tokens = set(tokens)
        for token in unique_tokens:
            self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
            
        self.total_docs = len(self.documents)
        self.avg_doc_length = sum(self.doc_lengths.values()) / self.total_docs if self.total_docs > 0 else 0.0
        
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search documents using BM25."""
        if not self.documents:
            return []
            
        query_tokens = self._tokenize(query)
        scores = {}
        
        for doc_id, text in self.documents.items():
            score = 0.0
            doc_length = self.doc_lengths[doc_id]
            tokens = self._tokenize(text)
            token_counts = {}
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1
                
            for token in query_tokens:
                if token in self.doc_freqs:
                    idf = np.log((self.total_docs - self.doc_freqs[token] + 0.5) / 
                                (self.doc_freqs[token] + 0.5) + 1.0)
                    tf = token_counts.get(token, 0)
                    score += idf * ((tf * (self.k1 + 1)) / 
                                   (tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))))
            
            if score > 0:
                scores[doc_id] = score
                
        # Sort by score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for doc_id, score in sorted_results:
            results.append({
                "id": doc_id,
                "text": self.documents[doc_id],
                "score": score,
            })
        return results


class HybridSearcher:
    """Combines vector similarity and BM25 keyword search."""
    
    def __init__(self, vector_weight: float = 0.7, keyword_weight: float = 0.3):
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.bm25 = BM25Searcher()
        
    def normalize_scores(self, results: List[Dict[str, Any]], score_key: str = "score") -> List[Dict[str, Any]]:
        """Normalize scores to 0-1 range using min-max normalization."""
        if not results:
            return results
            
        scores = [r[score_key] for r in results]
        min_score, max_score = min(scores), max(scores)
        
        if max_score == min_score:
            for r in results:
                r[score_key] = 1.0
        else:
            for r in results:
                r[score_key] = (r[score_key] - min_score) / (max_score - min_score)
                
        return results
        
    def combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Combine and re-rank results from vector and keyword search.
        
        Args:
            vector_results: Results from vector similarity search
            keyword_results: Results from BM25 keyword search
            top_k: Number of top results to return
            
        Returns:
            Combined and re-ranked results
        """
        # Convert vector distances to scores (1 - distance)
        for r in vector_results:
            r["score"] = 1 - r.get("distance", 0)
            
        # Normalize scores
        vector_results = self.normalize_scores(vector_results, "score")
        keyword_results = self.normalize_scores(keyword_results, "score")
        
        # Combine scores using Reciprocal Rank Fusion (RRF)
        combined = {}
        k = 60  # RRF constant
        
        # Add vector scores
        for rank, result in enumerate(vector_results):
            doc_id = result["id"]
            if doc_id not in combined:
                combined[doc_id] = {"result": result, "rrf_score": 0}
            combined[doc_id]["rrf_score"] += self.vector_weight / (k + rank + 1)
            
        # Add keyword scores
        for rank, result in enumerate(keyword_results):
            doc_id = result["id"]
            if doc_id not in combined:
                combined[doc_id] = {"result": result, "rrf_score": 0}
            combined[doc_id]["rrf_score"] += self.keyword_weight / (k + rank + 1)
            
        # Sort by RRF score
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )[:top_k]
        
        # Return combined results with metadata
        final_results = []
        for item in sorted_results:
            result = item["result"].copy()
            result["hybrid_score"] = item["rrf_score"]
            result["source"] = "hybrid"
            final_results.append(result)
            
        return final_results
