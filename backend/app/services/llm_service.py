# backend/app/services/llm_service.py
"""
LLM service with support for Grok and Claude APIs
"""

import logging
import asyncio
import httpx
from typing import Dict, Any, AsyncGenerator, Optional, List
import json

from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.config = settings
        self.logger = logger
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize HTTP client for API calls"""
        self.client = httpx.AsyncClient(timeout=60.0)
        
        if self.config.llm_provider == "grok":
            self.api_url = "https://api.x.ai/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.config.grok_api_key}",
                "Content-Type": "application/json"
            }
            self.model = self.config.grok_model
            
        elif self.config.llm_provider == "claude":
            self.api_url = "https://api.anthropic.com/v1/messages"
            self.headers = {
                "x-api-key": self.config.claude_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            self.model = self.config.claude_model
            
        elif self.config.llm_provider == "openai":
            self.api_url = "https://api.openai.com/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.config.openai_api_key}",
                "Content-Type": "application/json"
            }
            self.model = self.config.openai_model
    
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

            if self.config.llm_provider == "grok":
                return await self._generate_grok_response(system_prompt, user_message, conversation_history)
            elif self.config.llm_provider == "claude":
                return await self._generate_claude_response(system_prompt, user_message, conversation_history)
            elif self.config.llm_provider == "openai":
                return await self._generate_openai_response(system_prompt, user_message, conversation_history)
            else:
                raise Exception(f"Unsupported LLM provider: {self.config.llm_provider}")
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            raise
    
    async def _generate_grok_response(self, system_prompt: str, user_message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """Generate response using Grok API"""
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if history:
                messages.extend(history[-10:])  # Last 10 messages
            
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
    
    async def _generate_claude_response(self, system_prompt: str, user_message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """Generate response using Claude API"""
        try:
            # Claude uses a different message format
            messages = []
            
            if history:
                # Convert history to Claude format
                for msg in history[-10:]:
                    if msg['role'] != 'system':
                        messages.append({
                            "role": msg['role'],
                            "content": msg['content']
                        })
            
            messages.append({
                "role": "user", 
                "content": f"{system_prompt}\n\nUser: {user_message}"
            })
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.1
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
                raise Exception(f"Claude API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error with Claude API: {e}")
            raise
    
    async def _generate_openai_response(self, system_prompt: str, user_message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """Generate response using OpenAI API"""
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if history:
                messages.extend(history[-10:])
            
            messages.append({"role": "user", "content": user_message})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 500
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
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.logger.error(f"Error with OpenAI API: {e}")
            raise
    
    async def generate_response_stream(
        self,
        user_message: str,
        context: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        try:
            # For now, implement streaming for OpenAI and Grok, fallback to chunks for Claude
            if self.config.llm_provider in ["openai", "grok"]:
                async for chunk in self._generate_streaming_response(user_message, context, conversation_history):
                    yield chunk
            else:
                # Fallback: get full response and yield it in chunks
                response = await self.generate_response(user_message, context, conversation_history)
                words = response['response'].split()
                for i in range(0, len(words), 3):  # Yield 3 words at a time
                    chunk = ' '.join(words[i:i+3]) + ' '
                    yield chunk
                    await asyncio.sleep(0.05)  # Small delay for streaming effect
                    
        except Exception as e:
            self.logger.error(f"Error in streaming response: {e}")
            yield f"Error: {str(e)}"
    
    async def _generate_streaming_response(self, user_message: str, context: str, history: List[Dict] = None) -> AsyncGenerator[str, None]:
        """Generate streaming response for supported providers"""
        try:
            system_prompt = f"""You are VexaAI, an intelligent assistant specialized in answering questions about PDF documents.
You have been developed by John Evans Okyere to provide accurate, concise, and helpful responses.

Instructions:
1. Use ONLY the provided context to answer questions
2. If the context doesn't contain sufficient information, clearly state "I don't have enough information in the provided document to answer this question."
3. Keep responses concise and limit to a maximum of three sentences unless more detail is specifically requested
4. Do not make up information or use external knowledge
5. Be professional and helpful in your responses

Context: {context}"""

            messages = [{"role": "system", "content": system_prompt}]
            if history:
                messages.extend(history[-10:])
            messages.append({"role": "user", "content": user_message})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 500,
                "stream": True
            }
            
            async with self.client.stream(
                "POST",
                self.api_url,
                headers=self.headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        line = line[6:]  # Remove "data: " prefix
                        if line.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(line)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            self.logger.error(f"Error in streaming response: {e}")
            yield f"Error: {str(e)}"
    
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

