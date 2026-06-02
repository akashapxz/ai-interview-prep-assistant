"""
Unit Tests for RAG Engine Chunks & Indexing
"""

import pytest
from src.ai.rag_engine import chunk_text

def test_chunk_text():
    text = "Hello world. This is a simple document text to verify if chunking works correctly and splits paragraphs into parts."
    chunks = chunk_text(text)
    assert len(chunks) >= 1
    assert any("Hello world" in c for c in chunks)
