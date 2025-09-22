# backend/app/services/cloud_chat_service.py
"""
Complete cloud chat service - replaces your original chat_engine.py
"""

import logging
from typing import Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from app.config import settings
from app.database import get_supabase_client
from app.services.vector_service import VectorService

if settings.llm_provider == "openai":
    import openai
elif settings.llm_provider == "anthropic":
    from anthropic import Anthropic
elif settings.llm_provider == "cohere":
    import cohere

logger = logging.getLogger(__name__)

class ChatService:
    """Cloud replacement for your original ChatEngine"""
    
    def __init__(self):
        self.config = settings
        self.supabase = get_supabase_client()
        self.vector_service = VectorService()
        self.logger = logger
        self._initialize_llm_client()
    
    def _initialize_llm_client(self):
        """Initialize LLM client based on provider"""
        try:
            if self.config.llm_provider == "openai":
                self.llm_client = openai.AsyncOpenAI(api_key=self.config.openai_api_key)
                self.model_name = self.config.openai_model
                
            elif self.config.llm_provider == "anthropic":
                self.llm_client = Anthropic(api_key=self.config.anthropic_api_key)
                self.model_name = self.config.anthropic_model
                
            elif self.config.llm_provider == "cohere":
                self.llm_client = cohere.AsyncClient(api_key=self.config.cohere_api_key)
                self.model_name = self.config.cohere_model
                
            self.logger.info(f"Initialized LLM with provider: {self.config.llm_provider}")
            
        except Exception as e:
            self.logger.error(f"Error initializing LLM client: {e}")
            raise
    
    def _preprocess_question(self, question: str) -> str:
        """Preprocess user question (from your original)"""
        question = question.strip()
        if question and not question.endswith(('?', '.', '!')):
            question += '?'
        return question
    
    def _validate_question(self, question: str) -> bool:
        """Validate user question (from your original)"""
        if not question or not question.strip():
            return False
        if len(question.strip()) < 3:
            return False
        return True
    
    async def _get_context_for_question(self, question: str, document_ids: Optional[list] = None) -> str:
        """Retrieve relevant context (adapted from your original)"""
        try:
            context = await self.vector_service.get_relevant_context(
                question,
                document_ids,
                max_context_length=self.config.max_context_length
            )
            self.logger.debug(f"Retrieved context of length: {len(context)}")
            return context
        except Exception as e:
            self.logger.error(f"Error retrieving context: {e}")
            return "Error retrieving relevant context."
    
    async def _generate_response(self, question: str, context: str) -> Dict[str, Any]:
        """Generate response using cloud LLM (replaces your Ollama logic)"""
        try:
            # Your original system prompt
            system_prompt = f"""You are VexaAI, an intelligent assistant specialized in answering questions about PDF documents.
You have been developed by John Evans Okyere to provide accurate, concise, and helpful responses.

Instructions:
1. Use ONLY the provided context to answer questions
2. If the context doesn't contain sufficient information, clearly state "I don't have enough information in the provided document to answer this question."
3. Keep responses concise and limit to a maximum of three sentences unless more detail is specifically requested
4. Do not make up information or use external knowledge
5. Be professional and helpful in your responses
6. If asked about topics outside the document, politely redirect to document-related questions

Context: {context}"""

            if self.config.llm_provider == "openai":
                response = await self.llm_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                return {
                    'response': response.choices[0].message.content,
                    'tokens_used': response.usage.total_tokens,
                    'model': self.model_name
                }
                
            elif self.config.llm_provider == "anthropic":
                full_prompt = f"{system_prompt}\n\nHuman: {question}\n\nAssistant:"
                
                response = await self.llm_client.messages.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                
                return {
                    'response': response.content[0].text,
                    'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                    'model': self.model_name
                }
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return {
                'response': "I apologize, but I'm having trouble generating a response right now. Please try again.",
                'tokens_used': 0,
                'model': self.model_name
            }
    
    def _postprocess_response(self, response: str) -> str:
        """Post-process response (from your original)"""
        response = response.strip()
        if self.config.max_response_length > 0:
            if len(response) > self.config.max_response_length:
                response = response[:self.config.max_response_length] + "..."
        return response
    
    async def get_response(self, question: str, document_ids: Optional[list] = None) -> Dict[str, Any]:
        """Main method to get response (adapted from your original)"""
        start_time = datetime.utcnow()
        
        try:
            # Preprocess question
            question = self._preprocess_question(question)
            
            # Validate question
            if not self._validate_question(question):
                return {
                    'response': "Please provide a valid question to get started.",
                    'tokens_used': 0,
                    'processing_time': 0,
                    'context_chunks': []
                }
            
            self.logger.info(f"Processing question: '{question[:100]}...'")
            
            # Get relevant context
            context = await self._get_context_for_question(question, document_ids)
            
            # Generate response
            llm_response = await self._generate_response(question, context)
            
            # Post-process response
            processed_response = self._postprocess_response(llm_response['response'])
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'response': processed_response,
                'tokens_used': llm_response.get('tokens_used', 0),
                'processing_time': processing_time,
                'model': llm_response.get('model', self.model_name),
                'context_chunks': []  # Will be populated by vector service
            }
            
            self.logger.info(f"Generated response in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in get_response: {e}")
            return {
                'response': f"I apologize, but I encountered an error while processing your question: {str(e)}",
                'tokens_used': 0,
                'processing_time': (datetime.utcnow() - start_time).total_seconds(),
                'context_chunks': []
            }
    
    async def test_llm_connection(self) -> bool:
        """Test LLM connection (from your original)"""
        try:
            test_response = await self._generate_response(
                "Hello, please respond with 'Connection successful'", 
                ""
            )
            
            if test_response['response'] and len(test_response['response'].strip()) > 0:
                self.logger.info("LLM connection test passed")
                return True
            else:
                self.logger.error("LLM connection test failed: empty response")
                return False
                
        except Exception as e:
            self.logger.error(f"LLM connection test failed: {e}")
            return False
    
    def get_suggested_questions(self, context: str) -> list:
        """Generate suggested questions (from your original)"""
        suggestions = [
            "What is the main topic of this document?",
            "Can you summarize the key points?", 
            "What are the most important findings?",
            "Are there any specific recommendations mentioned?",
            "What conclusions can be drawn from this document?"
        ]
        return suggestions[:3]



