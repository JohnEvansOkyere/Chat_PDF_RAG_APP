# backend/app/services/llm_service.py
"""
LLM service with support for Grok, Claude, and OpenAI APIs.
This service abstracts provider-specific API calls behind a unified interface
to generate responses from different Large Language Models (LLMs).
"""

import logging
import asyncio
import httpx
from typing import Dict, Any, AsyncGenerator, List
import json

from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for managing LLM API calls.
    
    Supports:
        - Grok (xAI)
        - Claude (Anthropic)
        - OpenAI GPT models
    
    Provides:
        - Unified response generation interface
        - Streaming responses (simulated, extendable later)
        - Connection test utility
    """
    def __init__(self):
        self.config = settings
        self.logger = logger
        self._initialize_client()
    
    def _initialize_client(self):
        """
        Initialize HTTP client and configure API details 
        (endpoint, headers, and default model) based on the selected provider.
        """
        self.client = httpx.AsyncClient(timeout=60.0)

        provider = self.config.llm_provider.lower()

        # Configure each provider
        if provider == "grok":
            self.api_url = "https://api.x.ai/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.config.grok_api_key}",
                "Content-Type": "application/json"
            }
            self.model = self.config.grok_model or "grok-beta"

        elif provider == "claude":
            self.api_url = "https://api.anthropic.com/v1/messages"
            self.headers = {
                "x-api-key": self.config.claude_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            self.model = self.config.claude_model or "claude-3-sonnet-20240229"

        elif provider == "openai":
            self.api_url = "https://api.openai.com/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.config.openai_api_key}",
                "Content-Type": "application/json"
            }
            self.model = self.config.openai_model or "gpt-4o-mini"

        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.llm_provider}")
    
    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using the configured LLM provider.
        
        Args:
            user_message (str): The user query or prompt.
            context (str): Context text (e.g., retrieved from RAG pipeline).
            conversation_history (List[Dict]): Previous chat exchanges.
        
        Returns:
            Dict[str, Any]: Model response, tokens used, provider, etc.
        """
        try:
            # System prompt defines assistant rules and formatting
            system_prompt = f"""You are VexaAI, an intelligent assistant specialized in answering questions about PDF documents.
                You have been developed by John Evans Okyere to provide accurate, concise, and helpful responses.

                CRITICAL FORMATTING RULES:
                - Write in plain text only - NO asterisks (*), hash symbols (#), or any special characters for formatting
                - DO NOT use markdown formatting like **bold** or *italic* Take note of this
                - DO NOT add citation references like "(Cited from Chunk 1)" or similar
                - DO NOT mention chunks, sections, or document structure
                - Write naturally as if speaking to someone - no technical formatting

                Instructions:
                1. Use ONLY the provided context to answer questions
                2. If the context doesn't contain sufficient information, clearly state "I don't have enough information in the provided document to answer this question."
                3. Keep responses concise and limit to a maximum of 200 words unless more detail is specifically requested
                4. Do not make up information or use external knowledge beyond the provided context
                5. Be professional and helpful in your responses
                6. If asked about topics outside the document, politely redirect to document-related questions
                7. Reference information naturally without any formatting or citation patterns
                8. Write in simple, clean paragraphs without special symbols

                Context from document: {context}"""

            # Dispatch request to the correct provider
            provider = self.config.llm_provider.lower()
            if provider == "grok":
                return await self._generate_grok_response(system_prompt, user_message, conversation_history)
            elif provider == "claude":
                return await self._generate_claude_response(system_prompt, user_message, conversation_history)
            elif provider == "openai":
                return await self._generate_openai_response(system_prompt, user_message, conversation_history)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.config.llm_provider}")
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            raise
    
    async def _generate_grok_response(self, system_prompt: str, user_message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        Generate response using Grok API.
        Includes last 8 conversation turns for continuity.
        """
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if history:
                messages.extend(history[-8:])  # Keep last 8 exchanges
            
            messages.append({"role": "user", "content": user_message})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1000,
                "stream": False,
                "top_p": 0.9
            }
            
            response = await self.client.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'response': data['choices'][0]['message']['content'],
                    'tokens_used': data.get('usage', {}).get('total_tokens', 0),
                    'model': self.model,
                    'provider': 'grok'
                }
            else:
                self.logger.error(f"Grok API error: {response.status_code} - {response.text}")
                raise Exception(f"Grok API error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error with Grok API: {e}")
            raise
    
    async def _generate_claude_response(self, system_prompt: str, user_message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        Generate response using Claude API.
        Uses Anthropic's `messages` endpoint.
        """
        try:
            messages = []
            
            if history:
                messages.extend(history[-8:])  # Keep last 8 exchanges
            
            messages.append({"role": "user", "content": user_message})
            
            payload = {
                "model": self.model,
                "max_tokens": 1000,
                "temperature": 0.3,
                "system": system_prompt,
                "messages": messages
            }
            
            response = await self.client.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'response': data['content'][0]['text'],
                    'tokens_used': data.get('usage', {}).get('input_tokens', 0) + data.get('usage', {}).get('output_tokens', 0),
                    'model': self.model,
                    'provider': 'claude'
                }
            else:
                self.logger.error(f"Claude API error: {response.status_code} - {response.text}")
                raise Exception(f"Claude API error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error with Claude API: {e}")
            raise
    
    async def _generate_openai_response(self, system_prompt: str, user_message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        Generate response using OpenAI API.
        Uses Chat Completions endpoint.
        """
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if history:
                messages.extend(history[-8:])  # Keep last 8 exchanges
            
            messages.append({"role": "user", "content": user_message})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1000,
                "top_p": 0.9,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
            
            response = await self.client.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'response': data['choices'][0]['message']['content'],
                    'tokens_used': data.get('usage', {}).get('total_tokens', 0),
                    'model': self.model,
                    'provider': 'openai'
                }
            else:
                self.logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenAI API error: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error with OpenAI API: {e}")
            raise

    async def test_connection(self) -> str:
        """
        Test LLM connection by sending a simple probe message.
        
        Returns:
            str: LLM response text confirming successful connection.
        """
        try:
            response = await self.generate_response("Hello, please respond with 'Connection successful'")
            return response['response']
        except Exception as e:
            self.logger.error(f"LLM connection test failed: {e}")
            raise
    
    async def generate_streaming_response(
        self,
        user_message: str,
        context: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response (simulated).
        Currently streams the response word by word with delay.
        Can be replaced with true server-sent events or WebSocket in production.
        """
        try:
            # First, generate a full response
            response = await self.generate_response(user_message, context, conversation_history)
            
            # Stream word by word for UI effect
            words = response['response'].split()
            for word in words:
                yield f"{word} "
                await asyncio.sleep(0.05)  # Artificial delay for realism
                
        except Exception as e:
            self.logger.error(f"Streaming response failed: {e}")
            yield f"Error: {str(e)}"
    
    async def __aenter__(self):
        """Support async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensure httpx client is properly closed"""
        await self.client.aclose()
