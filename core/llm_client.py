"""
Rika Phase 3.4 LLM Client System
Multi-provider support: Anthropic Claude, OpenAI GPT, Local (Ollama)
"""
import asyncio
import json
import httpx
from typing import AsyncGenerator, Dict, Any, Optional, List
from abc import ABC, abstractmethod
from .config import RikaConfig

class LLMMessage:
    """Standardized message format across all LLM providers"""
    def __init__(self, role: str, content: str, tool_calls: Optional[List] = None):
        self.role = role  # system, user, assistant
        self.content = content
        self.tool_calls = tool_calls or []

class LLMResponse:
    """Standardized response format"""
    def __init__(self, content: str = "", finished: bool = False, tool_calls: Optional[List] = None, error: Optional[str] = None):
        self.content = content
        self.finished = finished
        self.tool_calls = tool_calls or []
        self.error = error

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    def __init__(self, config: RikaConfig):
        self.config = config
    
    @abstractmethod
    async def chat_stream(self, messages: List[LLMMessage], **kwargs) -> AsyncGenerator[LLMResponse, None]:
        """Stream chat responses"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Non-streaming chat response"""
        pass

class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client with streaming support"""
    
    def __init__(self, config: RikaConfig):
        super().__init__(config)
        if not config.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
        
        self.client = httpx.AsyncClient(
            base_url="https://api.anthropic.com/v1",
            headers={
                "x-api-key": config.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
    
    def _format_messages(self, messages: List[LLMMessage]) -> tuple:
        """Format messages for Anthropic API"""
        system_message = ""
        formatted_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return system_message, formatted_messages
    
    async def chat_stream(self, messages: List[LLMMessage], **kwargs) -> AsyncGenerator[LLMResponse, None]:
        """Stream responses from Claude"""
        system_msg, formatted_messages = self._format_messages(messages)
        
        payload = {
            "model": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "messages": formatted_messages,
            "stream": True
        }
        
        if system_msg:
            payload["system"] = system_msg
        
        try:
            async with self.client.stream("POST", "/messages", json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield LLMResponse(error=f"Anthropic API error: {response.status_code} - {error_text.decode()}")
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            yield LLMResponse(finished=True)
                            return
                        
                        try:
                            event = json.loads(data)
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    yield LLMResponse(content=text)
                            elif event.get("type") == "message_stop":
                                yield LLMResponse(finished=True)
                                return
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            yield LLMResponse(error=f"Anthropic streaming error: {str(e)}")
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Non-streaming response from Claude"""
        system_msg, formatted_messages = self._format_messages(messages)
        
        payload = {
            "model": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "messages": formatted_messages,
        }
        
        if system_msg:
            payload["system"] = system_msg
        
        try:
            response = await self.client.post("/messages", json=payload)
            if response.status_code != 200:
                return LLMResponse(error=f"Anthropic API error: {response.status_code} - {response.text}")
            
            data = response.json()
            content = ""
            if data.get("content"):
                for block in data["content"]:
                    if block.get("type") == "text":
                        content += block.get("text", "")
            
            return LLMResponse(content=content, finished=True)
            
        except Exception as e:
            return LLMResponse(error=f"Anthropic error: {str(e)}")

class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client with streaming support"""
    
    def __init__(self, config: RikaConfig):
        super().__init__(config)
        if not config.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={
                "Authorization": f"Bearer {config.openai_api_key}",
                "Content-Type": "application/json"
            }
        )
    
    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict]:
        """Format messages for OpenAI API"""
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    async def chat_stream(self, messages: List[LLMMessage], **kwargs) -> AsyncGenerator[LLMResponse, None]:
        """Stream responses from GPT"""
        formatted_messages = self._format_messages(messages)
        
        payload = {
            "model": self.config.model_name if self.config.model_name.startswith("gpt-") else "gpt-3.5-turbo",
            "messages": formatted_messages,
            "max_tokens": self.config.max_tokens,
            "stream": True
        }
        
        try:
            async with self.client.stream("POST", "/chat/completions", json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield LLMResponse(error=f"OpenAI API error: {response.status_code} - {error_text.decode()}")
                    return
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            yield LLMResponse(finished=True)
                            return
                        
                        try:
                            event = json.loads(data)
                            choices = event.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield LLMResponse(content=content)
                                
                                if choices[0].get("finish_reason"):
                                    yield LLMResponse(finished=True)
                                    return
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            yield LLMResponse(error=f"OpenAI streaming error: {str(e)}")
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Non-streaming response from GPT"""
        formatted_messages = self._format_messages(messages)
        
        payload = {
            "model": self.config.model_name if self.config.model_name.startswith("gpt-") else "gpt-3.5-turbo",
            "messages": formatted_messages,
            "max_tokens": self.config.max_tokens
        }
        
        try:
            response = await self.client.post("/chat/completions", json=payload)
            if response.status_code != 200:
                return LLMResponse(error=f"OpenAI API error: {response.status_code} - {response.text}")
            
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                return LLMResponse(content=content, finished=True)
            
            return LLMResponse(error="No response from OpenAI")
            
        except Exception as e:
            return LLMResponse(error=f"OpenAI error: {str(e)}")

class LocalLLMClient(BaseLLMClient):
    """Local LLM client (Ollama or compatible endpoint)"""
    
    def __init__(self, config: RikaConfig):
        super().__init__(config)
        self.client = httpx.AsyncClient(
            base_url=config.local_base_url,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )
    
    def _format_messages(self, messages: List[LLMMessage]) -> str:
        """Format messages for local LLM (simple text format)"""
        formatted = ""
        for msg in messages:
            if msg.role == "system":
                formatted += f"System: {msg.content}\n\n"
            elif msg.role == "user":
                formatted += f"Human: {msg.content}\n\n"
            elif msg.role == "assistant":
                formatted += f"Assistant: {msg.content}\n\n"
        
        formatted += "Assistant: "
        return formatted
    
    async def chat_stream(self, messages: List[LLMMessage], **kwargs) -> AsyncGenerator[LLMResponse, None]:
        """Stream responses from local LLM (fallback to non-streaming)"""
        # Many local LLMs don't support streaming, so we'll simulate it
        response = await self.chat(messages, **kwargs)
        if response.error:
            yield response
            return
        
        # Simulate streaming by yielding chunks
        words = response.content.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield LLMResponse(content=chunk)
            await asyncio.sleep(0.05)  # Small delay to simulate streaming
        
        yield LLMResponse(finished=True)
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Non-streaming response from local LLM"""
        prompt = self._format_messages(messages)
        
        # Try Ollama format first
        payload = {
            "model": self.config.local_model_name,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = await self.client.post("/api/generate", json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data.get("response", "")
                return LLMResponse(content=content, finished=True)
            else:
                return LLMResponse(error=f"Local LLM API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            return LLMResponse(error=f"Local LLM error: {str(e)}")

class LLMClientFactory:
    """Factory for creating LLM clients based on configuration"""
    
    @staticmethod
    def create_client(config: RikaConfig) -> BaseLLMClient:
        """Create appropriate LLM client based on config"""
        provider = config.llm_provider.lower()
        
        if provider == "anthropic":
            return AnthropicClient(config)
        elif provider == "openai":
            return OpenAIClient(config)
        elif provider == "local":
            return LocalLLMClient(config)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}. Supported: anthropic, openai, local")

# Global client instance will be created when needed
_client_instance: Optional[BaseLLMClient] = None

def get_llm_client(config: RikaConfig) -> BaseLLMClient:
    """Get or create the global LLM client instance"""
    global _client_instance
    if _client_instance is None:
        _client_instance = LLMClientFactory.create_client(config)
    return _client_instance