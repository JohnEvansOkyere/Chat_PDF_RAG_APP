# backend/app/services/llm_service.py
"""
LLM service with support for Grok, Claude, and OpenAI APIs
"""

import logging
import asyncio
import httpx
from typing import Dict, Any, AsyncGenerator, List
import json

from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.config = settings
        self.logger = logger
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize HTTP client and API details based on provider"""
        self.client = httpx.AsyncClient(timeout=60.0)

        provider = self.config.llm_provider.lower()

        if provider == "grok":
            self.api_url = "https://api.x.ai/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.config.grok_api_key}",
                "Content-Type": "application/json"
            }
            self.model = self.config.grok_model or "grok-4-fast-reasoning"

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
        """Generate response using configured LLM provider"""
        try:
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
        """Generate response using Grok API"""
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if history:
                messages.extend(history[-10:])  # Keep last 10 exchanges
            
            messages.append({"role": "user", "content": user_message})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 500,
                "stream": False
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
                raise Exception(f"Grok API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error with Grok API: {e}")
            raise

    async def test_connection(self) -> str:
        """Test LLM connection"""
        try:
            response = await self.generate_response("Hello, please respond with 'Connection successful'")
            return response['response']
        except Exception as e:
            self.logger.error(f"LLM connection test failed: {e}")
            raise
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
