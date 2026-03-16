from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import os
import json
import logging

from api.core.config import settings

logger = logging.getLogger(__name__)

# Load env from JSON file (local dev) or use os.environ (Render, Docker, etc.)
# json_env_path = os.path.join(os.path.dirname(__file__), '../.env/vars.json')
# if os.path.exists(json_env_path):
#     try:
#         with open(json_env_path) as f:
#             env_vars = json.load(f)
#         for k, v in env_vars.items():
#             if v:
#                 os.environ[k] = str(v)
#     except Exception:
#         pass
# When JSON not found: use platform env vars - no action needed

class LLMBackend(ABC):
    """Abstract base class for LLM backends"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    async def generate_with_tools(self, prompt: str, tools: List[Any], **kwargs) -> Dict[str, Any]:
        """Generate text with tool calling"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass

class OpenAIBackend(LLMBackend):
    """OpenAI LLM backend"""
    
    def __init__(self, model: str = "gpt-4-turbo-preview", temperature: float = 0.7):
        # Import lazily so local/unit tests can run without optional deps installed.
        try:
            from langchain_openai import ChatOpenAI  # type: ignore
        except Exception as e:
            raise ImportError(
                "Missing optional dependency `langchain_openai`. "
                "Install it (or run within the project venv) to use OpenAIBackend."
            ) from e

        self.model = model
        self.temperature = temperature
        self.api_key = settings.OPENAI_API_KEY
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=self.api_key
        )
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI"""
        try:
            response = await self.llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    async def generate_with_tools(self, prompt: str, tools: List[Any], **kwargs) -> Dict[str, Any]:
        """Generate text with tool calling using OpenAI"""
        try:
            # For now, return a simple response
            # In a full implementation, this would handle tool calling
            response = await self.llm.ainvoke(prompt)
            return {
                "content": response.content,
                "tools_used": [],
                "model": self.model
            }
        except Exception as e:
            logger.error(f"OpenAI tool generation failed: {e}")
            raise
    
    async def ainvoke(self, prompt: str) -> Any:
        """Async invoke method for compatibility"""
        return await self.llm.ainvoke(prompt)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information"""
        return {
            "provider": "OpenAI",
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": 4096
        }

class GeminiBackend(LLMBackend):
    """Google Gemini LLM backend"""
    
    def __init__(self, model: str = "gemini-pro", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        # Note: Would need langchain_google_genai for full implementation
        self.llm = None  # Placeholder
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini"""
        try:
            # Placeholder implementation
            return f"Gemini response to: {prompt[:100]}..."
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise
    
    async def generate_with_tools(self, prompt: str, tools: List[Any], **kwargs) -> Dict[str, Any]:
        """Generate text with tool calling using Gemini"""
        try:
            # Placeholder implementation
            return {
                "content": f"Gemini tool response to: {prompt[:100]}...",
                "tools_used": [],
                "model": self.model
            }
        except Exception as e:
            logger.error(f"Gemini tool generation failed: {e}")
            raise
    
    async def ainvoke(self, prompt: str) -> Any:
        """Async invoke method for compatibility"""
        return type('obj', (object,), {'content': await self.generate(prompt)})()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Gemini model information"""
        return {
            "provider": "Google",
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": 8192
        }

def get_llm_backend(provider: str = "openai", **kwargs) -> LLMBackend:
    """Factory function to get LLM backend"""
    if provider.lower() == "openai":
        return OpenAIBackend(**kwargs)
    elif provider.lower() == "gemini":
        return GeminiBackend(**kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}") 