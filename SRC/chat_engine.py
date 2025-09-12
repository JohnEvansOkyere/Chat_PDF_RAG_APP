"""
Chat Engine Module for VexaAI RAG Chat PDF Application
Handles conversation logic and response generation
Developed by: John Evans Okyere
"""
import logging
from typing import List, Dict, Optional
import time
from datetime import datetime

from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

class ChatEngine:
    """Handles chat interactions and response generation"""
    
    def __init__(self, config, vector_store_manager):
        """
        Initialize chat engine with configuration and vector store
        
        Args:
            config: Configuration object
            vector_store_manager: Vector store manager instance
        """
        self.config = config
        self.vector_store_manager = vector_store_manager
        self.llm = self._create_llm()
        self.prompt_template = self._create_prompt_template()
        self.logger = self._setup_logger()
        self.conversation_history = []
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for chat engine"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _create_llm(self) -> OllamaLLM:
        """Create and configure Ollama LLM"""
        try:
            llm = OllamaLLM(
                model=self.config.MODEL_NAME,
                base_url=self.config.OLLAMA_BASE_URL,
                temperature=self.config.TEMPERATURE
            )
            self.logger.info(f"Initialized LLM with model: {self.config.MODEL_NAME}")
            return llm
        except Exception as e:
            self.logger.error(f"Error creating LLM: {str(e)}")
            raise
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create and configure prompt template"""
        return ChatPromptTemplate.from_template(self.config.SYSTEM_PROMPT)
    
    def _preprocess_question(self, question: str) -> str:
        """
        Preprocess user question before processing
        
        Args:
            question: Raw user question
            
        Returns:
            str: Preprocessed question
        """
        # Basic preprocessing
        question = question.strip()
        
        # Add question mark if missing
        if question and not question.endswith(('?', '.', '!')):
            question += '?'
        
        return question
    
    def _validate_question(self, question: str) -> bool:
        """
        Validate user question
        
        Args:
            question: User question to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not question or not question.strip():
            return False
        
        # Check minimum length
        if len(question.strip()) < 3:
            return False
        
        return True
    
    def _get_context_for_question(self, question: str) -> str:
        """
        Retrieve relevant context for a question
        
        Args:
            question: User question
            
        Returns:
            str: Relevant context
        """
        try:
            # Get relevant context from vector store
            context = self.vector_store_manager.get_relevant_context(
                question,
                max_context_length=2000
            )
            
            self.logger.debug(f"Retrieved context of length: {len(context)}")
            return context
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {str(e)}")
            return "Error retrieving relevant context."
    
    def _generate_response(self, question: str, context: str) -> str:
        """
        Generate response using LLM
        
        Args:
            question: User question
            context: Relevant context
            
        Returns:
            str: Generated response
        """
        try:
            # Create prompt chain
            chain = self.prompt_template | self.llm
            
            # Generate response
            response = chain.invoke({
                "question": question,
                "context": context
            })
            
            # Post-process response
            response = self._postprocess_response(response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    def _postprocess_response(self, response: str) -> str:
        """
        Post-process generated response
        
        Args:
            response: Raw response from LLM
            
        Returns:
            str: Processed response
        """
        # Clean up response
        response = response.strip()
        
        # Limit response length if configured
        if hasattr(self.config, 'MAX_RESPONSE_LENGTH') and self.config.MAX_RESPONSE_LENGTH > 0:
            if len(response) > self.config.MAX_RESPONSE_LENGTH:
                response = response[:self.config.MAX_RESPONSE_LENGTH] + "..."
        
        return response
    
    def get_response(self, question: str) -> str:
        """
        Main method to get response for a user question
        
        Args:
            question: User question
            
        Returns:
            str: Response to the question
        """
        start_time = time.time()
        
        try:
            # Preprocess question
            question = self._preprocess_question(question)
            
            # Validate question
            if not self._validate_question(question):
                return "Please provide a valid question to get started."
            
            # Check if vector store is ready
            if not self.vector_store_manager.is_ready():
                return "Please upload and process a PDF document first before asking questions."
            
            self.logger.info(f"Processing question: '{question[:100]}...'")
            
            # Get relevant context
            context = self._get_context_for_question(question)
            
            # Generate response
            response = self._generate_response(question, context)
            
            # Record conversation
            processing_time = time.time() - start_time
            self._record_conversation(question, response, context, processing_time)
            
            self.logger.info(f"Generated response in {processing_time:.2f} seconds")
            return response
            
        except Exception as e:
            self.logger.error(f"Error in get_response: {str(e)}")
            return f"I apologize, but I encountered an error while processing your question: {str(e)}"
    
    def _record_conversation(self, question: str, response: str, context: str, processing_time: float):
        """
        Record conversation for history tracking
        
        Args:
            question: User question
            response: Generated response
            context: Retrieved context
            processing_time: Time taken to process
        """
        conversation_entry = {
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'response': response,
            'context_length': len(context),
            'processing_time': processing_time,
            'model_used': self.config.MODEL_NAME
        }
        
        self.conversation_history.append(conversation_entry)
        
        # Keep only last N conversations to prevent memory issues
        max_history = getattr(self.config, 'MAX_CONVERSATION_HISTORY', 50)
        if len(self.conversation_history) > max_history:
            self.conversation_history = self.conversation_history[-max_history:]
    
    def get_conversation_history(self) -> List[Dict]:
        """
        Get conversation history
        
        Returns:
            List[Dict]: List of conversation entries
        """
        return self.conversation_history.copy()
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.logger.info("Cleared conversation history")
    
    def get_conversation_stats(self) -> Dict:
        """
        Get conversation statistics
        
        Returns:
            Dict: Statistics about conversations
        """
        if not self.conversation_history:
            return {
                'total_conversations': 0,
                'average_processing_time': 0,
                'total_processing_time': 0
            }
        
        total_conversations = len(self.conversation_history)
        processing_times = [entry['processing_time'] for entry in self.conversation_history]
        
        stats = {
            'total_conversations': total_conversations,
            'average_processing_time': sum(processing_times) / len(processing_times),
            'total_processing_time': sum(processing_times),
            'fastest_response': min(processing_times),
            'slowest_response': max(processing_times),
            'model_used': self.config.MODEL_NAME
        }
        
        return stats
    
    def test_llm_connection(self) -> bool:
        """
        Test LLM connection
        
        Returns:
            bool: True if connection works, False otherwise
        """
        try:
            test_prompt = "Hello, please respond with 'Connection successful'"
            response = self.llm.invoke(test_prompt)
            
            if response and len(response.strip()) > 0:
                self.logger.info("LLM connection test passed")
                return True
            else:
                self.logger.error("LLM connection test failed: empty response")
                return False
                
        except Exception as e:
            self.logger.error(f"LLM connection test failed: {str(e)}")
            return False
    
    def get_suggested_questions(self, context: str) -> List[str]:
        """
        Generate suggested questions based on context
        
        Args:
            context: Document context
            
        Returns:
            List[str]: List of suggested questions
        """
        # Basic suggested questions based on common patterns
        suggestions = [
            "What is the main topic of this document?",
            "Can you summarize the key points?",
            "What are the most important findings?",
            "Are there any specific recommendations mentioned?",
            "What conclusions can be drawn from this document?"
        ]
        
        return suggestions[:3]  # Return top 3 suggestions