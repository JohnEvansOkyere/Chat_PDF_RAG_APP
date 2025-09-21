import pytest
from langchain_core.documents import Document
from src.vector_store import VectorStoreManager

# ------------------
# Dummy Config
# ------------------
class DummyConfig:
    EMBEDDING_MODEL = "llama3.2:1b"   # fake Ollama model name
    OLLAMA_BASE_URL = "http://localhost:11434"
    SIMILARITY_SEARCH_K = 2
    RELEVANCE_THRESHOLD = 0.0  # keep all results

@pytest.fixture
def vector_store_manager():
    """Fixture to create a VectorStoreManager instance"""
    return VectorStoreManager(DummyConfig)

@pytest.fixture
def sample_documents():
    """Fixture with fake documents"""
    return [
        Document(page_content="Python is a programming language", metadata={"source_file": "doc1.pdf", "page_number": 1}),
        Document(page_content="Machine learning enables AI applications", metadata={"source_file": "doc1.pdf", "page_number": 2}),
        Document(page_content="Data science uses Python and ML", metadata={"source_file": "doc2.pdf", "page_number": 1}),
    ]

# ------------------
# Tests
# ------------------

def test_index_documents(vector_store_manager, sample_documents):
    result = vector_store_manager.index_documents(sample_documents)
    assert result is True
    stats = vector_store_manager.get_index_stats()
    assert stats["total_documents"] == 3
    assert stats["has_documents"] is True

def test_similarity_search(vector_store_manager, sample_documents):
    vector_store_manager.index_documents(sample_documents)
    results = vector_store_manager.similarity_search("What is Python?")
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(doc, Document) for doc in results)

def test_similarity_search_with_scores(vector_store_manager, sample_documents):
    vector_store_manager.index_documents(sample_documents)
    results = vector_store_manager.similarity_search_with_scores("AI and ML")
    assert isinstance(results, list)
    assert len(results) > 0
    for doc, score in results:
        assert isinstance(doc, Document)
        assert isinstance(score, float)

def test_get_relevant_context(vector_store_manager, sample_documents):
    vector_store_manager.index_documents(sample_documents)
    context = vector_store_manager.get_relevant_context("Python and ML", max_context_length=200)
    assert isinstance(context, str)
    assert "Python" in context or "ML" in context

def test_clear_index(vector_store_manager, sample_documents):
    vector_store_manager.index_documents(sample_documents)
    vector_store_manager.clear_index()
    stats = vector_store_manager.get_index_stats()
    assert stats["total_documents"] == 0
    assert stats["has_documents"] is False

def test_add_single_document(vector_store_manager):
    doc = Document(page_content="Single document test", metadata={"source_file": "single.pdf", "page_number": 1})
    result = vector_store_manager.add_single_document(doc)
    assert result is True
    stats = vector_store_manager.get_index_stats()
    assert stats["total_documents"] == 1

def test_remove_documents_by_source(vector_store_manager, sample_documents):
    vector_store_manager.index_documents(sample_documents)
    result = vector_store_manager.remove_documents_by_source("doc1.pdf")
    assert result is True
    stats = vector_store_manager.get_index_stats()
    assert stats["total_documents"] == 1
    assert "doc2.pdf" in stats["source_files"]

def test_is_ready(vector_store_manager, sample_documents):
    assert vector_store_manager.is_ready() is False
    vector_store_manager.index_documents(sample_documents)
    assert vector_store_manager.is_ready() is True

def test_test_embeddings(vector_store_manager):
    result = vector_store_manager.test_embeddings()
    assert isinstance(result, bool)
