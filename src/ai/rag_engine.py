"""
RAG Engine — LangChain + FAISS + Sentence Transformers
Handles document chunking, embedding, vector search, and answer generation.
"""

import os
import json
import logging
import pickle
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv

from src.database.supabase_client import (
    get_supabase_client, db_insert, db_select, db_update
)
from src.ai.prompts import RAG_ANSWER_PROMPT

load_dotenv()
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))
FAISS_CACHE_DIR = Path("faiss_indexes")
FAISS_CACHE_DIR.mkdir(exist_ok=True)


@st.cache_resource
def _get_embeddings() -> HuggingFaceEmbeddings:
    """Load sentence-transformer embeddings (cached globally)."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


# ─────────────────────────────────────────────
# Text chunking
# ─────────────────────────────────────────────

def chunk_text(text: str) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


# ─────────────────────────────────────────────
# Index management (per-user FAISS index)
# ─────────────────────────────────────────────

def _index_path(user_id: str) -> Path:
    safe_id = hashlib.md5(user_id.encode()).hexdigest()[:16]
    return FAISS_CACHE_DIR / f"user_{safe_id}"


def build_user_index(user_id: str, texts: List[str], metadatas: List[Dict]) -> FAISS:
    """Build a FAISS vector store from a list of text chunks."""
    embeddings = _get_embeddings()
    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    path = _index_path(user_id)
    vectorstore.save_local(str(path))
    return vectorstore


def load_user_index(user_id: str) -> Optional[FAISS]:
    """Load an existing FAISS index from disk."""
    try:
        path = _index_path(user_id)
        if not path.exists():
            return None
        embeddings = _get_embeddings()
        return FAISS.load_local(str(path), embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        logger.error(f"load_user_index error: {e}")
        return None


def add_document_to_index(user_id: str, text: str, doc_metadata: Dict) -> int:
    """Add a new document's chunks to the user's FAISS index. Returns chunk count."""
    chunks = chunk_text(text)
    if not chunks:
        return 0

    metadatas = [{"source": doc_metadata.get("file_name", "unknown"), **doc_metadata}
                 for _ in chunks]

    embeddings = _get_embeddings()
    existing = load_user_index(user_id)

    if existing:
        existing.add_texts(chunks, metadatas=metadatas)
        existing.save_local(str(_index_path(user_id)))
        vectorstore = existing
    else:
        vectorstore = build_user_index(user_id, chunks, metadatas)

    return len(chunks)


# ─────────────────────────────────────────────
# Retrieval + Answer generation
# ─────────────────────────────────────────────

def retrieve_relevant_chunks(
    user_id: str, query: str, k: int = 5
) -> List[Tuple[str, Dict]]:
    """Return top-k relevant chunks from user's vector store."""
    vectorstore = load_user_index(user_id)
    if not vectorstore:
        return []
    try:
        docs = vectorstore.similarity_search_with_score(query, k=k)
        return [(doc.page_content, doc.metadata) for doc, score in docs if score < 1.5]
    except Exception as e:
        logger.error(f"retrieve_relevant_chunks error: {e}")
        return []


def answer_from_rag(user_id: str, question: str) -> Dict:
    """Answer a question using RAG pipeline. Returns answer + sources."""
    chunks = retrieve_relevant_chunks(user_id, question, k=5)

    if not chunks:
        return {
            "answer": "I couldn't find relevant information in your uploaded documents. Please upload some study materials first.",
            "sources": [],
            "chunks_used": 0,
        }

    context_parts = []
    sources = set()
    for chunk_text, metadata in chunks:
        context_parts.append(chunk_text)
        if "source" in metadata:
            sources.add(metadata["source"])

    context = "\n\n---\n\n".join(context_parts)
    prompt = RAG_ANSWER_PROMPT.format(context=context, question=question)

    from src.ai.gemini_client import generate_text
    answer = generate_text(prompt, temperature=0.3)

    return {
        "answer": answer,
        "sources": list(sources),
        "chunks_used": len(chunks),
        "context_preview": context[:300] + "...",
    }


# ─────────────────────────────────────────────
# Document indexing workflow
# ─────────────────────────────────────────────

def index_document(user_id: str, doc_id: str, text: str, file_name: str, doc_type: str) -> bool:
    """Full pipeline: chunk → embed → store in FAISS → update DB."""
    try:
        metadata = {
            "doc_id": doc_id,
            "file_name": file_name,
            "doc_type": doc_type,
            "user_id": user_id,
        }
        chunk_count = add_document_to_index(user_id, text, metadata)

        # Store chunks in DB for reference
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            db_insert("knowledge_base", {
                "document_id": doc_id,
                "user_id": user_id,
                "chunk_text": chunk,
                "chunk_index": i,
                "metadata": metadata,
            })

        # Mark document as indexed
        db_update("uploaded_documents", {"id": doc_id}, {
            "is_indexed": True,
            "chunk_count": chunk_count,
        })
        return True
    except Exception as e:
        logger.error(f"index_document error: {e}")
        return False


def rebuild_user_index_from_db(user_id: str) -> bool:
    """Rebuild FAISS index from DB chunks (for recovery after cache loss)."""
    try:
        chunks_data = db_select("knowledge_base", {"user_id": user_id})
        if not chunks_data:
            return False

        texts = [c["chunk_text"] for c in chunks_data]
        metadatas = [c.get("metadata", {}) for c in chunks_data]

        embeddings = _get_embeddings()
        vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
        vectorstore.save_local(str(_index_path(user_id)))
        return True
    except Exception as e:
        logger.error(f"rebuild_user_index_from_db error: {e}")
        return False
