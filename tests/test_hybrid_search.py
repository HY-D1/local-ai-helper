"""Tests for hybrid search functionality."""
import pytest
from src.memory.hybrid_search import BM25Searcher, HybridSearcher


class TestBM25Searcher:
    """Tests for BM25 keyword search."""
    
    def test_empty_search(self):
        searcher = BM25Searcher()
        results = searcher.search("test")
        assert results == []
        
    def test_single_document(self):
        searcher = BM25Searcher()
        searcher.add_document("doc1", "The quick brown fox")
        results = searcher.search("fox")
        assert len(results) == 1
        assert results[0]["id"] == "doc1"
        
    def test_multiple_documents(self):
        searcher = BM25Searcher()
        searcher.add_document("doc1", "The quick brown fox")
        searcher.add_document("doc2", "The lazy dog")
        searcher.add_document("doc3", "Another fox jumps")
        
        results = searcher.search("fox")
        assert len(results) == 2
        # Both docs with "fox" should be returned
        ids = [r["id"] for r in results]
        assert "doc1" in ids
        assert "doc3" in ids
        
    def test_relevance_ranking(self):
        searcher = BM25Searcher()
        searcher.add_document("doc1", "fox fox fox")  # More occurrences
        searcher.add_document("doc2", "fox")  # Single occurrence
        
        results = searcher.search("fox")
        assert len(results) == 2
        # doc1 should rank higher due to more occurrences
        assert results[0]["id"] == "doc1"
        
    def test_tokenization(self):
        searcher = BM25Searcher()
        searcher.add_document("doc1", "HELLO World")
        results = searcher.search("hello")
        assert len(results) == 1  # Should be case-insensitive


class TestHybridSearcher:
    """Tests for hybrid search combining vector and keyword."""
    
    def test_normalize_scores(self):
        searcher = HybridSearcher()
        results = [
            {"id": "doc1", "score": 10},
            {"id": "doc2", "score": 5},
            {"id": "doc3", "score": 0},
        ]
        normalized = searcher.normalize_scores(results)
        
        assert normalized[0]["score"] == 1.0  # Max becomes 1.0
        assert normalized[2]["score"] == 0.0  # Min becomes 0.0
        assert normalized[1]["score"] == 0.5  # Middle becomes 0.5
        
    def test_normalize_empty(self):
        searcher = HybridSearcher()
        results = []
        normalized = searcher.normalize_scores(results)
        assert normalized == []
        
    def test_combine_results(self):
        searcher = HybridSearcher(vector_weight=0.7, keyword_weight=0.3)
        
        vector_results = [
            {"id": "doc1", "text": "text1", "distance": 0.1},
            {"id": "doc2", "text": "text2", "distance": 0.2},
        ]
        keyword_results = [
            {"id": "doc2", "text": "text2", "score": 10},
            {"id": "doc3", "text": "text3", "score": 5},
        ]
        
        combined = searcher.combine_results(vector_results, keyword_results, top_k=3)
        
        # Should have 3 unique documents
        assert len(combined) == 3
        # All should have hybrid_score
        for r in combined:
            assert "hybrid_score" in r
            assert "source" in r
            assert r["source"] == "hybrid"
            
    def test_combine_results_overlap(self):
        searcher = HybridSearcher()
        
        # Same document in both results
        vector_results = [
            {"id": "doc1", "text": "text1", "distance": 0.1},
        ]
        keyword_results = [
            {"id": "doc1", "text": "text1", "score": 10},
        ]
        
        combined = searcher.combine_results(vector_results, keyword_results, top_k=1)
        
        assert len(combined) == 1
        # Should have combined score
        assert combined[0]["id"] == "doc1"
        
    def test_combine_empty_results(self):
        searcher = HybridSearcher()
        combined = searcher.combine_results([], [], top_k=10)
        assert combined == []
