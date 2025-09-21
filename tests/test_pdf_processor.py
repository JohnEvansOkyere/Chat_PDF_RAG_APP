"""
Enhanced unit tests for PDFProcessor module
Tests PDF processing, text extraction, and document chunking
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from src.pdf_processor import PDFProcessor
from langchain_core.documents import Document


# --- Mock Config ---
class MockConfig:
    CHUNK_SIZE = 100
    CHUNK_OVERLAP = 20
    MAX_FILE_SIZE_MB = 5  # 5 MB


@pytest.fixture
def pdf_processor():
    """Create PDFProcessor instance with mock config"""
    return PDFProcessor(config=MockConfig)


@pytest.fixture
def sample_documents():
    """Create fake langchain Document objects for testing splitting & stats."""
    return [
        Document(
            page_content="This is a test page one with some content that should be split properly.", 
            metadata={"source_file": "test.pdf", "page_number": 1}
        ),
        Document(
            page_content="This is page two with more text content that also needs proper handling.", 
            metadata={"source_file": "test.pdf", "page_number": 2}
        ),
    ]


@pytest.fixture
def large_sample_documents():
    """Create documents that will definitely need splitting"""
    long_content = "A" * 200  # Longer than CHUNK_SIZE (100)
    return [
        Document(
            page_content=long_content,
            metadata={"source_file": "test.pdf", "page_number": 1}
        )
    ]


@pytest.fixture
def empty_documents():
    """Create empty documents for edge case testing"""
    return []


# --- Validation Tests ---
def test_validate_pdf_file_with_nonexistent_file(pdf_processor):
    """Test validation fails for non-existent file"""
    assert not pdf_processor.validate_pdf_file("fake.pdf")


def test_validate_pdf_file_with_wrong_extension(pdf_processor, tmp_path):
    """Test validation fails for non-PDF files"""
    txt_file = tmp_path / "fake.txt"
    txt_file.write_text("hello")
    assert not pdf_processor.validate_pdf_file(str(txt_file))


def test_validate_pdf_file_with_large_file(pdf_processor, tmp_path):
    """Test validation fails for files exceeding size limit"""
    pdf_file = tmp_path / "large.pdf"
    pdf_file.write_bytes(b"0" * (6 * 1024 * 1024))  # 6 MB
    assert not pdf_processor.validate_pdf_file(str(pdf_file))


def test_validate_pdf_file_with_valid_file(pdf_processor, tmp_path):
    """Test validation passes for valid PDF file"""
    pdf_file = tmp_path / "valid.pdf"
    pdf_file.write_bytes(b"PDF content here")  # Small valid file
    assert pdf_processor.validate_pdf_file(str(pdf_file))


def test_validate_pdf_file_with_case_insensitive_extension(pdf_processor, tmp_path):
    """Test validation works with different case extensions"""
    pdf_file1 = tmp_path / "test.PDF"
    pdf_file2 = tmp_path / "test.Pdf"
    pdf_file1.write_bytes(b"PDF content")
    pdf_file2.write_bytes(b"PDF content")
    
    assert pdf_processor.validate_pdf_file(str(pdf_file1))
    assert pdf_processor.validate_pdf_file(str(pdf_file2))


@patch('os.path.exists', side_effect=Exception("OS Error"))
def test_validate_pdf_file_with_exception(mock_exists, pdf_processor):
    """Test validation handles exceptions gracefully"""
    assert not pdf_processor.validate_pdf_file("any_file.pdf")


# --- Document Splitting Tests ---
def test_split_documents_adds_metadata(pdf_processor, sample_documents):
    """Test that document splitting adds proper chunk metadata"""
    chunks = pdf_processor.split_documents(sample_documents)
    assert isinstance(chunks, list)
    assert len(chunks) > 0
    
    # Check first chunk has required metadata
    first_chunk = chunks[0]
    assert "chunk_id" in first_chunk.metadata
    assert "total_chunks" in first_chunk.metadata
    assert "chunk_size" in first_chunk.metadata
    
    # Check chunk_id ordering
    for i, chunk in enumerate(chunks):
        assert chunk.metadata["chunk_id"] == i
        assert chunk.metadata["total_chunks"] == len(chunks)


def test_split_documents_empty_list(pdf_processor, empty_documents):
    """Test splitting empty document list"""
    chunks = pdf_processor.split_documents(empty_documents)
    assert chunks == []


def test_split_documents_with_long_content(pdf_processor, large_sample_documents):
    """Test that long documents are properly split"""
    chunks = pdf_processor.split_documents(large_sample_documents)
    assert len(chunks) > 1  # Should be split into multiple chunks
    
    # Verify chunk sizes are reasonable
    for chunk in chunks:
        assert len(chunk.page_content) <= MockConfig.CHUNK_SIZE + MockConfig.CHUNK_OVERLAP


@patch('src.pdf_processor.RecursiveCharacterTextSplitter.split_documents')
def test_split_documents_handles_exception(mock_split, pdf_processor, sample_documents):
    """Test that splitting handles exceptions properly"""
    mock_split.side_effect = Exception("Splitting failed")
    
    with pytest.raises(Exception, match="Failed to split documents"):
        pdf_processor.split_documents(sample_documents)


# --- PDF Loading Tests ---
@patch('src.pdf_processor.PDFPlumberLoader')
def test_load_pdf_success(mock_loader_class, pdf_processor, tmp_path):
    """Test successful PDF loading"""
    # Create a valid PDF file
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"PDF content")
    
    # Mock the loader
    mock_loader = Mock()
    mock_documents = [
        Document(page_content="Test content", metadata={})
    ]
    mock_loader.load.return_value = mock_documents
    mock_loader_class.return_value = mock_loader
    
    result = pdf_processor.load_pdf(str(pdf_file))
    
    assert len(result) == 1
    assert result[0].metadata["source_file"] == "test.pdf"
    assert result[0].metadata["page_number"] == 1
    assert result[0].metadata["total_pages"] == 1


def test_load_pdf_invalid_file(pdf_processor):
    """Test loading invalid PDF file"""
    try:
        pdf_processor.load_pdf("nonexistent.pdf")
        assert False, "Expected exception but none was raised"
    except Exception as e:
        assert "Failed to load PDF" in str(e)


@patch('src.pdf_processor.PDFPlumberLoader')
def test_load_pdf_no_content(mock_loader_class, pdf_processor, tmp_path):
    """Test loading PDF with no content"""
    pdf_file = tmp_path / "empty.pdf"
    pdf_file.write_bytes(b"PDF")
    
    mock_loader = Mock()
    mock_loader.load.return_value = []
    mock_loader_class.return_value = mock_loader
    
    try:
        pdf_processor.load_pdf(str(pdf_file))
        assert False, "Expected exception but none was raised"
    except Exception as e:
        assert "Failed to load PDF" in str(e)


@patch('src.pdf_processor.PDFPlumberLoader')
def test_load_pdf_loader_exception(mock_loader_class, pdf_processor, tmp_path):
    """Test PDF loading when loader throws exception"""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"PDF")
    
    mock_loader = Mock()
    mock_loader.load.side_effect = Exception("Loader failed")
    mock_loader_class.return_value = mock_loader
    
    with pytest.raises(Exception, match="Failed to load PDF"):
        pdf_processor.load_pdf(str(pdf_file))


# --- Complete Processing Pipeline Tests ---
@patch('src.pdf_processor.PDFPlumberLoader')
def test_process_pdf_complete_pipeline(mock_loader_class, pdf_processor, tmp_path):
    """Test complete PDF processing pipeline"""
    # Setup
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(b"PDF content")
    
    mock_loader = Mock()
    mock_documents = [
        Document(page_content="This is test content that should be processed", metadata={})
    ]
    mock_loader.load.return_value = mock_documents
    mock_loader_class.return_value = mock_loader
    
    # Test
    result = pdf_processor.process_pdf(str(pdf_file))
    
    # Verify
    assert isinstance(result, list)
    assert len(result) > 0
    assert "chunk_id" in result[0].metadata
    assert "source_file" in result[0].metadata


def test_process_pdf_propagates_exceptions(pdf_processor):
    """Test that process_pdf propagates exceptions from sub-methods"""
    try:
        pdf_processor.process_pdf("nonexistent.pdf")
        assert False, "Expected exception but none was raised"
    except Exception as e:
        assert "Failed to load PDF" in str(e)


# --- Statistics Tests ---
def test_get_document_stats(pdf_processor, sample_documents):
    """Test document statistics calculation"""
    chunks = pdf_processor.split_documents(sample_documents)
    stats = pdf_processor.get_document_stats(chunks)
    
    assert stats["total_chunks"] == len(chunks)
    assert "total_characters" in stats
    assert "total_words" in stats
    assert "average_chunk_size" in stats
    assert stats["chunk_size_config"] == MockConfig.CHUNK_SIZE
    assert stats["chunk_overlap_config"] == MockConfig.CHUNK_OVERLAP
    assert isinstance(stats["source_files"], list)


def test_get_document_stats_empty_documents(pdf_processor, empty_documents):
    """Test statistics with empty document list"""
    stats = pdf_processor.get_document_stats(empty_documents)
    assert stats == {}


def test_get_document_stats_calculations(pdf_processor):
    """Test that statistics calculations are correct"""
    test_docs = [
        Document(page_content="Hello world", metadata={"source_file": "test1.pdf", "page_number": 1}),
        Document(page_content="Test doc", metadata={"source_file": "test2.pdf", "page_number": 1}),
    ]
    
    stats = pdf_processor.get_document_stats(test_docs)
    
    assert stats["total_chunks"] == 2
    assert stats["total_characters"] == 19  # "Hello world" (11) + "Test doc" (8)
    assert stats["total_words"] == 4  # 2 + 2 words
    assert stats["average_chunk_size"] == 9  # 19 // 2


# --- Text Preview Tests ---
def test_extract_text_preview(pdf_processor, sample_documents):
    """Test text preview extraction"""
    chunks = pdf_processor.split_documents(sample_documents)
    preview = pdf_processor.extract_text_preview(chunks, max_length=50)
    
    assert isinstance(preview, str)
    assert len(preview) <= 53  # 50 + "..."


def test_extract_text_preview_empty(pdf_processor):
    """Test text preview with empty documents"""
    assert pdf_processor.extract_text_preview([]) == "No content available"


def test_extract_text_preview_long_content(pdf_processor):
    """Test text preview truncation with long content"""
    long_docs = [
        Document(page_content="A" * 100, metadata={}),
        Document(page_content="B" * 100, metadata={}),
    ]
    
    preview = pdf_processor.extract_text_preview(long_docs, max_length=50)
    assert len(preview) <= 53  # 50 + "..."
    assert preview.endswith("...")


def test_extract_text_preview_short_content(pdf_processor):
    """Test text preview with short content (no truncation)"""
    short_docs = [
        Document(page_content="Short", metadata={})
    ]
    
    preview = pdf_processor.extract_text_preview(short_docs, max_length=50)
    assert preview == "Short"
    assert not preview.endswith("...")


# --- Initialization Tests ---
def test_pdf_processor_initialization(pdf_processor):
    """Test PDFProcessor proper initialization"""
    assert pdf_processor.config == MockConfig
    assert pdf_processor.text_splitter is not None
    assert pdf_processor.logger is not None


def test_text_splitter_configuration(pdf_processor):
    """Test text splitter is configured correctly"""
    splitter = pdf_processor.text_splitter
    # Test that the splitter was created with the right class and basic functionality
    assert splitter is not None
    assert hasattr(splitter, 'split_documents')
    
    # Test that it works as expected by splitting a test document
    test_doc = Document(page_content="A" * 200)  # Long content
    result = splitter.split_documents([test_doc])
    
    # Should split into multiple chunks for long content
    assert len(result) > 1
    
    # Each chunk should be reasonably sized (around chunk_size)
    for chunk in result:
        assert len(chunk.page_content) <= MockConfig.CHUNK_SIZE + 50  # Some tolerance


def test_logger_setup(pdf_processor):
    """Test logger setup"""
    logger = pdf_processor._setup_logger()
    assert logger.name == "src.pdf_processor"
    assert logger.level == 20  # INFO level


# --- Edge Cases and Error Handling ---
def test_split_documents_preserves_original_metadata(pdf_processor):
    """Test that splitting preserves original document metadata"""
    docs_with_metadata = [
        Document(
            page_content="Test content", 
            metadata={"custom_field": "custom_value", "source_file": "test.pdf"}
        )
    ]
    
    chunks = pdf_processor.split_documents(docs_with_metadata)
    
    # Original metadata should be preserved
    assert chunks[0].metadata["custom_field"] == "custom_value"
    assert chunks[0].metadata["source_file"] == "test.pdf"
    
    # New metadata should be added
    assert "chunk_id" in chunks[0].metadata
    assert "total_chunks" in chunks[0].metadata


def test_get_document_stats_with_missing_metadata(pdf_processor):
    """Test statistics calculation with missing metadata fields"""
    docs_no_metadata = [
        Document(page_content="Content without metadata", metadata={}),
        Document(page_content="More content", metadata={"source_file": "test.pdf"}),
    ]
    
    stats = pdf_processor.get_document_stats(docs_no_metadata)
    
    assert stats["total_chunks"] == 2
    assert "unknown" in stats["source_files"]  # Default for missing source_file
    assert "test.pdf" in stats["source_files"]


# --- Integration-like Tests ---
def test_full_workflow_with_realistic_content(pdf_processor):
    """Test a more realistic workflow with proper content"""
    # Simulate documents that would come from a real PDF
    realistic_docs = [
        Document(
            page_content="""
            Chapter 1: Introduction to Machine Learning
            
            Machine learning is a subset of artificial intelligence that focuses on algorithms
            that can learn and improve from experience without being explicitly programmed.
            This field has seen tremendous growth in recent years.
            """.strip(),
            metadata={"source_file": "ml_book.pdf", "page_number": 1}
        ),
        Document(
            page_content="""
            Chapter 2: Types of Machine Learning
            
            There are three main types of machine learning: supervised learning, 
            unsupervised learning, and reinforcement learning. Each type has its own
            applications and use cases in different domains.
            """.strip(),
            metadata={"source_file": "ml_book.pdf", "page_number": 2}
        )
    ]
    
    # Split documents
    chunks = pdf_processor.split_documents(realistic_docs)
    
    # Get stats
    stats = pdf_processor.get_document_stats(chunks)
    
    # Get preview
    preview = pdf_processor.extract_text_preview(chunks, max_length=100)
    
    # Verify everything worked
    assert len(chunks) >= 2  # Should have at least original number of docs
    assert stats["total_chunks"] == len(chunks)
    assert stats["source_files"] == ["ml_book.pdf"]
    assert "Chapter 1" in preview or "Machine learning" in preview


def test_sanity():
    """Basic sanity check"""
    assert 1 + 1 == 2