import os
import tempfile
import pytest
from pathlib import Path
from src.pdf_processor import PDFProcessor
from langchain_core.documents import Document

# --- Mock Config ---
class MockConfig:
    CHUNK_SIZE = 100
    CHUNK_OVERLAP = 20
    MAX_FILE_SIZE_MB = 5  # 5 MB


@pytest.fixture
def pdf_processor():
    return PDFProcessor(config=MockConfig)


@pytest.fixture
def sample_documents():
    """Create fake langchain Document objects for testing splitting & stats."""
    return [
        Document(page_content="This is a test page one.", metadata={"source_file": "test.pdf", "page_number": 1}),
        Document(page_content="This is page two with more text.", metadata={"source_file": "test.pdf", "page_number": 2}),
    ]


def test_validate_pdf_file_with_nonexistent_file(pdf_processor):
    assert not pdf_processor.validate_pdf_file("fake.pdf")


def test_validate_pdf_file_with_wrong_extension(pdf_processor, tmp_path):
    txt_file = tmp_path / "fake.txt"
    txt_file.write_text("hello")
    assert not pdf_processor.validate_pdf_file(str(txt_file))


def test_validate_pdf_file_with_large_file(pdf_processor, tmp_path):
    pdf_file = tmp_path / "large.pdf"
    pdf_file.write_bytes(b"0" * (6 * 1024 * 1024))  # 6 MB
    assert not pdf_processor.validate_pdf_file(str(pdf_file))


def test_split_documents_adds_metadata(pdf_processor, sample_documents):
    chunks = pdf_processor.split_documents(sample_documents)
    assert isinstance(chunks, list)
    assert "chunk_id" in chunks[0].metadata
    assert "total_chunks" in chunks[0].metadata


def test_get_document_stats(pdf_processor, sample_documents):
    chunks = pdf_processor.split_documents(sample_documents)
    stats = pdf_processor.get_document_stats(chunks)
    assert stats["total_chunks"] == len(chunks)
    assert "total_characters" in stats
    assert stats["chunk_size_config"] == MockConfig.CHUNK_SIZE


def test_extract_text_preview(pdf_processor, sample_documents):
    chunks = pdf_processor.split_documents(sample_documents)
    preview = pdf_processor.extract_text_preview(chunks, max_length=50)
    assert isinstance(preview, str)
    assert len(preview) <= 53  # 50 + "..."


def test_extract_text_preview_empty(pdf_processor):
    assert pdf_processor.extract_text_preview([]) == "No content available"


def test_sanity():
    assert 1 + 1 == 2

