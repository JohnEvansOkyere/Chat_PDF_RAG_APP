"""
Unit tests for ChatEngine module
Tests chat functionality, response generation, and conversation management
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
from datetime import datetime
import time

# Import the ChatEngine class
from src.chat_engine import ChatEngine


class TestChatEngine(unittest.TestCase):
    """Test cases for ChatEngine class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Mock configuration
        self.mock_config = Mock()
        self.mock_config.MODEL_NAME = "llama2"
        self.mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        self.mock_config.TEMPERATURE = 0.7
        self.mock_config.SYSTEM_PROMPT = "You are a helpful assistant. Context: {context}\n\nQuestion: {question}\n\nAnswer:"
        self.mock_config.MAX_RESPONSE_LENGTH = 1000
        self.mock_config.MAX_CONVERSATION_HISTORY = 50
        
        # Mock vector store manager
        self.mock_vector_store = Mock()
        self.mock_vector_store.is_ready.return_value = True
        self.mock_vector_store.get_relevant_context.return_value = "Sample context from PDF"
        
        # Create ChatEngine instance with mocked dependencies
        with patch('src.chat_engine.OllamaLLM') as mock_llm_class:
            self.mock_llm = Mock()
            mock_llm_class.return_value = self.mock_llm
            
            self.chat_engine = ChatEngine(self.mock_config, self.mock_vector_store)
    
    def test_init_success(self):
        """Test successful initialization of ChatEngine"""
        self.assertEqual(self.chat_engine.config, self.mock_config)
        self.assertEqual(self.chat_engine.vector_store_manager, self.mock_vector_store)
        self.assertIsNotNone(self.chat_engine.logger)
        self.assertIsNotNone(self.chat_engine.llm)
        self.assertIsNotNone(self.chat_engine.prompt_template)
        self.assertEqual(self.chat_engine.conversation_history, [])
    
    @patch('src.chat_engine.OllamaLLM')
    def test_create_llm_success(self, mock_llm_class):
        """Test successful LLM creation"""
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        chat_engine = ChatEngine(self.mock_config, self.mock_vector_store)
        
        mock_llm_class.assert_called_once_with(
            model=self.mock_config.MODEL_NAME,
            base_url=self.mock_config.OLLAMA_BASE_URL,
            temperature=self.mock_config.TEMPERATURE
        )
    
    @patch('src.chat_engine.OllamaLLM')
    def test_create_llm_failure(self, mock_llm_class):
        """Test LLM creation failure"""
        mock_llm_class.side_effect = Exception("Connection failed")
        
        with self.assertRaises(Exception) as context:
            ChatEngine(self.mock_config, self.mock_vector_store)
        
        self.assertIn("Connection failed", str(context.exception))
    
    def test_preprocess_question_basic(self):
        """Test basic question preprocessing"""
        # Test stripping whitespace
        result = self.chat_engine._preprocess_question("  What is AI?  ")
        self.assertEqual(result, "What is AI?")
        
        # Test adding question mark
        result = self.chat_engine._preprocess_question("Tell me about AI")
        self.assertEqual(result, "Tell me about AI?")
        
        # Test not adding question mark when already present
        result = self.chat_engine._preprocess_question("What is AI?")
        self.assertEqual(result, "What is AI?")
        
        # Test not adding question mark for statements ending with period
        result = self.chat_engine._preprocess_question("This is a statement.")
        self.assertEqual(result, "This is a statement.")
    
    def test_validate_question_valid(self):
        """Test question validation with valid inputs"""
        self.assertTrue(self.chat_engine._validate_question("What is AI?"))
        self.assertTrue(self.chat_engine._validate_question("How does this work?"))
        self.assertTrue(self.chat_engine._validate_question("ABC"))  # Minimum length
    
    def test_validate_question_invalid(self):
        """Test question validation with invalid inputs"""
        self.assertFalse(self.chat_engine._validate_question(""))
        self.assertFalse(self.chat_engine._validate_question("   "))
        self.assertFalse(self.chat_engine._validate_question("AB"))  # Too short
        self.assertFalse(self.chat_engine._validate_question(None))
    
    def test_get_context_for_question_success(self):
        """Test successful context retrieval"""
        question = "What is machine learning?"
        expected_context = "Machine learning context..."
        
        self.mock_vector_store.get_relevant_context.return_value = expected_context
        
        result = self.chat_engine._get_context_for_question(question)
        
        self.assertEqual(result, expected_context)
        self.mock_vector_store.get_relevant_context.assert_called_once_with(
            question, max_context_length=2000
        )
    
    def test_get_context_for_question_failure(self):
        """Test context retrieval failure"""
        question = "What is machine learning?"
        self.mock_vector_store.get_relevant_context.side_effect = Exception("DB Error")
        
        result = self.chat_engine._get_context_for_question(question)
        
        self.assertEqual(result, "Error retrieving relevant context.")
    
    def test_generate_response_success_with_content_attribute(self):
        """Test successful response generation with AIMessage-like object"""
        question = "What is AI?"
        context = "AI is artificial intelligence"
        expected_response = "AI stands for Artificial Intelligence"
        
        # Mock LLM response with content attribute (like AIMessage)
        mock_response = Mock()
        mock_response.content = expected_response
        
        # Mock the chain creation and invocation
        with patch.object(self.chat_engine, 'prompt_template') as mock_template:
            mock_chain = Mock()
            mock_template.__or__ = Mock(return_value=mock_chain)
            mock_chain.invoke.return_value = mock_response
            
            result = self.chat_engine._generate_response(question, context)
        
        self.assertEqual(result, expected_response)
    
    def test_generate_response_success_with_string(self):
        """Test successful response generation with string response"""
        question = "What is AI?"
        context = "AI is artificial intelligence"
        expected_response = "AI stands for Artificial Intelligence"
        
        # Mock the chain creation and invocation
        with patch.object(self.chat_engine, 'prompt_template') as mock_template:
            mock_chain = Mock()
            mock_template.__or__ = Mock(return_value=mock_chain)
            mock_chain.invoke.return_value = expected_response
            
            result = self.chat_engine._generate_response(question, context)
        
        self.assertEqual(result, expected_response)
    
    def test_generate_response_failure(self):
        """Test response generation failure"""
        question = "What is AI?"
        context = "AI is artificial intelligence"
        
        # Mock the chain creation and invocation to raise exception
        with patch.object(self.chat_engine, 'prompt_template') as mock_template:
            mock_chain = Mock()
            mock_template.__or__ = Mock(return_value=mock_chain)
            mock_chain.invoke.side_effect = Exception("LLM Error")
            
            result = self.chat_engine._generate_response(question, context)
        
        self.assertIn("I apologize, but I'm having trouble generating a response", result)
    
    def test_postprocess_response_basic(self):
        """Test basic response post-processing"""
        # Test stripping whitespace
        result = self.chat_engine._postprocess_response("  Response with spaces  ")
        self.assertEqual(result, "Response with spaces")
    
    def test_postprocess_response_length_limit(self):
        """Test response length limiting"""
        long_response = "A" * 1500  # Longer than MAX_RESPONSE_LENGTH
        
        result = self.chat_engine._postprocess_response(long_response)
        
        self.assertEqual(len(result), 1003)  # 1000 + "..."
        self.assertTrue(result.endswith("..."))
    
    def test_get_response_success(self):
        """Test successful complete response generation"""
        question = "What is machine learning?"
        expected_response = "Machine learning is a subset of AI"
        
        # Mock all the internal methods
        with patch.object(self.chat_engine, '_preprocess_question', return_value=question) as mock_preprocess, \
             patch.object(self.chat_engine, '_validate_question', return_value=True) as mock_validate, \
             patch.object(self.chat_engine, '_get_context_for_question', return_value="ML context") as mock_context, \
             patch.object(self.chat_engine, '_generate_response', return_value=expected_response) as mock_generate, \
             patch.object(self.chat_engine, '_record_conversation') as mock_record:
            
            result = self.chat_engine.get_response(question)
            
            self.assertEqual(result, expected_response)
            mock_preprocess.assert_called_once_with(question)
            mock_validate.assert_called_once_with(question)
            mock_context.assert_called_once_with(question)
            mock_generate.assert_called_once_with(question, "ML context")
            mock_record.assert_called_once()
    
    def test_get_response_invalid_question(self):
        """Test response with invalid question"""
        with patch.object(self.chat_engine, '_validate_question', return_value=False):
            result = self.chat_engine.get_response("")
            self.assertEqual(result, "Please provide a valid question to get started.")
    
    def test_get_response_vector_store_not_ready(self):
        """Test response when vector store is not ready"""
        self.mock_vector_store.is_ready.return_value = False
        
        result = self.chat_engine.get_response("What is AI?")
        
        self.assertEqual(result, "Please upload and process a PDF document first before asking questions.")
    
    def test_get_response_exception_handling(self):
        """Test exception handling in get_response"""
        question = "What is AI?"
        
        with patch.object(self.chat_engine, '_preprocess_question', side_effect=Exception("Test error")):
            result = self.chat_engine.get_response(question)
            
            self.assertIn("I apologize, but I encountered an error", result)
            self.assertIn("Test error", result)
    
    def test_record_conversation(self):
        """Test conversation recording"""
        question = "What is AI?"
        response = "AI is artificial intelligence"
        context = "Some context"
        processing_time = 1.5
        
        initial_count = len(self.chat_engine.conversation_history)
        
        self.chat_engine._record_conversation(question, response, context, processing_time)
        
        self.assertEqual(len(self.chat_engine.conversation_history), initial_count + 1)
        
        recorded = self.chat_engine.conversation_history[-1]
        self.assertEqual(recorded['question'], question)
        self.assertEqual(recorded['response'], response)
        self.assertEqual(recorded['context_length'], len(context))
        self.assertEqual(recorded['processing_time'], processing_time)
        self.assertEqual(recorded['model_used'], self.mock_config.MODEL_NAME)
        self.assertIn('timestamp', recorded)
    
    def test_record_conversation_history_limit(self):
        """Test conversation history limit enforcement"""
        self.mock_config.MAX_CONVERSATION_HISTORY = 2
        
        # Add 3 conversations
        for i in range(3):
            self.chat_engine._record_conversation(
                f"Question {i}",
                f"Response {i}",
                "context",
                1.0
            )
        
        # Should only keep the last 2
        self.assertEqual(len(self.chat_engine.conversation_history), 2)
        self.assertEqual(self.chat_engine.conversation_history[0]['question'], "Question 1")
        self.assertEqual(self.chat_engine.conversation_history[1]['question'], "Question 2")
    
    def test_get_conversation_history(self):
        """Test getting conversation history"""
        # Add a conversation
        self.chat_engine._record_conversation("Q1", "R1", "C1", 1.0)
        
        history = self.chat_engine.get_conversation_history()
        
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['question'], "Q1")
        # Ensure it returns a copy, not the original
        self.assertIsNot(history, self.chat_engine.conversation_history)
    
    def test_clear_conversation_history(self):
        """Test clearing conversation history"""
        # Add a conversation
        self.chat_engine._record_conversation("Q1", "R1", "C1", 1.0)
        self.assertEqual(len(self.chat_engine.conversation_history), 1)
        
        # Clear history
        self.chat_engine.clear_conversation_history()
        
        self.assertEqual(len(self.chat_engine.conversation_history), 0)
    
    def test_get_conversation_stats_empty(self):
        """Test getting conversation stats with empty history"""
        stats = self.chat_engine.get_conversation_stats()
        
        expected_stats = {
            'total_conversations': 0,
            'average_processing_time': 0,
            'total_processing_time': 0
        }
        self.assertEqual(stats, expected_stats)
    
    def test_get_conversation_stats_with_data(self):
        """Test getting conversation stats with data"""
        # Add conversations with different processing times
        processing_times = [1.0, 2.0, 3.0]
        for i, pt in enumerate(processing_times):
            self.chat_engine._record_conversation(f"Q{i}", f"R{i}", "C", pt)
        
        stats = self.chat_engine.get_conversation_stats()
        
        self.assertEqual(stats['total_conversations'], 3)
        self.assertEqual(stats['average_processing_time'], 2.0)
        self.assertEqual(stats['total_processing_time'], 6.0)
        self.assertEqual(stats['fastest_response'], 1.0)
        self.assertEqual(stats['slowest_response'], 3.0)
        self.assertEqual(stats['model_used'], self.mock_config.MODEL_NAME)
    
    def test_test_llm_connection_success(self):
        """Test successful LLM connection test"""
        self.mock_llm.invoke.return_value = "Connection successful"
        
        result = self.chat_engine.test_llm_connection()
        
        self.assertTrue(result)
        self.mock_llm.invoke.assert_called_once()
    
    def test_test_llm_connection_empty_response(self):
        """Test LLM connection test with empty response"""
        self.mock_llm.invoke.return_value = ""
        
        result = self.chat_engine.test_llm_connection()
        
        self.assertFalse(result)
    
    def test_test_llm_connection_exception(self):
        """Test LLM connection test with exception"""
        self.mock_llm.invoke.side_effect = Exception("Connection failed")
        
        result = self.chat_engine.test_llm_connection()
        
        self.assertFalse(result)
    
    def test_get_suggested_questions(self):
        """Test getting suggested questions"""
        context = "Some document context"
        
        suggestions = self.chat_engine.get_suggested_questions(context)
        
        self.assertIsInstance(suggestions, list)
        self.assertEqual(len(suggestions), 3)  # Should return top 3
        self.assertIn("What is the main topic of this document?", suggestions)
    
    def test_logger_setup(self):
        """Test logger setup"""
        logger = self.chat_engine._setup_logger()
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.level, 20)  # INFO level
    
    def test_prompt_template_creation(self):
        """Test prompt template creation"""
        template = self.chat_engine._create_prompt_template()
        
        self.assertIsNotNone(template)


class TestChatEngineIntegration(unittest.TestCase):
    """Integration tests for ChatEngine"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.mock_config = Mock()
        self.mock_config.MODEL_NAME = "llama2"
        self.mock_config.OLLAMA_BASE_URL = "http://localhost:11434"
        self.mock_config.TEMPERATURE = 0.7
        self.mock_config.SYSTEM_PROMPT = "Context: {context}\n\nQuestion: {question}\n\nAnswer:"
        self.mock_config.MAX_RESPONSE_LENGTH = 1000
        self.mock_config.MAX_CONVERSATION_HISTORY = 50
        
        self.mock_vector_store = Mock()
        self.mock_vector_store.is_ready.return_value = True
        self.mock_vector_store.get_relevant_context.return_value = "Test context"
    
    @patch('src.chat_engine.OllamaLLM')
    def test_full_conversation_flow(self, mock_llm_class):
        """Test complete conversation flow"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_response = Mock()
        mock_response.content = "This is a test response about AI"
        
        chat_engine = ChatEngine(self.mock_config, self.mock_vector_store)
        
        # Mock the chain creation and invocation
        with patch.object(chat_engine, 'prompt_template') as mock_template:
            mock_chain = Mock()
            mock_template.__or__ = Mock(return_value=mock_chain)
            mock_chain.invoke.return_value = mock_response
            
            # Test the complete flow
            question = "What is artificial intelligence"
            response = chat_engine.get_response(question)
            
            # Verify response
            self.assertEqual(response, "This is a test response about AI")
            
            # Verify conversation was recorded
            self.assertEqual(len(chat_engine.conversation_history), 1)
            recorded = chat_engine.conversation_history[0]
            self.assertEqual(recorded['question'], "What is artificial intelligence?")  # Note the added ?
            self.assertEqual(recorded['response'], "This is a test response about AI")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)