"""
LLM Inference Engine
Handles local LLM inference for Rika
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class RikaLLM:
    """Local LLM inference engine"""

    def __init__(self, model_path: str, n_ctx: int = 2048, n_threads: int = 8):
        """
        Initialize LLM inference engine

        Args:
            model_path: Path to LLM model file (GGUF format)
            n_ctx: Context window size
            n_threads: Number of CPU threads to use
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.model = None
        self.logger = logging.getLogger(__name__)

    def initialize(self):
        """Initialize the LLM model"""
        try:
            # Try to import llama-cpp-python
            try:
                from llama_cpp import Llama
                self.model = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_threads=self.n_threads,
                    verbose=False
                )
                self.logger.info(f"LLM loaded successfully: {self.model_path}")
                return True

            except ImportError:
                self.logger.warning(
                    "llama-cpp-python not installed. Using mock LLM for testing. "
                    "Install with: pip install llama-cpp-python"
                )
                self.model = MockLLM()
                return True

        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            self.model = MockLLM()
            return False

    def generate(self, prompt: str, max_tokens: int = 500,
                temperature: float = 0.3, **kwargs) -> str:
        """
        Generate response from prompt

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        try:
            if not self.model:
                self.initialize()

            # Check if using real model or mock
            if isinstance(self.model, MockLLM):
                return self.model.generate(prompt, max_tokens, temperature)

            # Real llama.cpp generation
            response = self.model(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=kwargs.get("top_p", 0.9),
                top_k=kwargs.get("top_k", 40),
                repeat_penalty=kwargs.get("repeat_penalty", 1.1),
                stop=kwargs.get("stop", ["USER:", "RESPONSE:", "\n\n\n"])
            )

            return response["choices"][0]["text"]

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "I encountered an error generating a response. Please try again."

    def tokenize(self, text: str) -> List[int]:
        """
        Convert text to tokens

        Args:
            text: Input text

        Returns:
            List of token IDs
        """
        try:
            if not self.model:
                self.initialize()

            if isinstance(self.model, MockLLM):
                # Simple word-based tokenization for mock
                return [hash(word) % 10000 for word in text.split()]

            return self.model.tokenize(text.encode())

        except Exception as e:
            self.logger.error(f"Error tokenizing text: {e}")
            return []

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Input text

        Returns:
            Token count
        """
        return len(self.tokenize(text))

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for text

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        try:
            if not self.model:
                self.initialize()

            if isinstance(self.model, MockLLM):
                return self.model.embed(text)

            # Use model's embedding if available
            if hasattr(self.model, 'embed'):
                return self.model.embed(text)

            # Fallback: simple hash-based embedding
            return self._simple_embedding(text)

        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return [0.0] * 384  # Return zero vector

    def _simple_embedding(self, text: str, dim: int = 384) -> List[float]:
        """
        Generate simple hash-based embedding

        Args:
            text: Input text
            dim: Embedding dimension

        Returns:
            Embedding vector
        """
        import hashlib

        # Generate deterministic embedding from text
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to float vector
        embedding = []
        for i in range(dim):
            byte_val = hash_bytes[i % len(hash_bytes)]
            embedding.append((byte_val / 255.0) * 2.0 - 1.0)  # Normalize to [-1, 1]

        return embedding

    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model

        Returns:
            Model info dict
        """
        return {
            "model_path": self.model_path,
            "context_size": self.n_ctx,
            "threads": self.n_threads,
            "loaded": self.model is not None,
            "type": "mock" if isinstance(self.model, MockLLM) else "llama.cpp"
        }


class MockLLM:
    """Mock LLM for testing when llama-cpp-python is not available"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate(self, prompt: str, max_tokens: int = 500,
                temperature: float = 0.3) -> str:
        """
        Generate mock response based on prompt

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens
            temperature: Temperature

        Returns:
            Mock response
        """
        # Simple rule-based responses for testing
        prompt_lower = prompt.lower()

        # Check for common patterns
        if "calendar" in prompt_lower or "schedule" in prompt_lower:
            return """Based on your calendar data, you typically have focus time in the mornings (9-11 AM)
and meetings in the afternoons. Your schedule is busiest on Tuesdays and Wednesdays.

REASONING: Retrieved calendar patterns from Cognitive Sphere
CONFIDENCE: 0.8"""

        elif "youtube" in prompt_lower or "video" in prompt_lower:
            return """Your recent YouTube videos show good engagement, with an average CTR of 5.2%.
The best performing content is your tutorial series.

ACTION: mint analyze_performance {"limit": 10}

REASONING: User asking about YouTube, delegating to Mint agent
CONFIDENCE: 0.9"""

        elif "email" in prompt_lower:
            return """Your email patterns show you prefer asynchronous communication and respond
quickly to work-related messages. Most emails are technical discussions and project coordination.

REASONING: Analyzed email communication patterns
CONFIDENCE: 0.75"""

        elif "project" in prompt_lower or "working on" in prompt_lower:
            return """Based on your recent activity, you're primarily working on the Rika automation
system and related infrastructure projects. Your coding style emphasizes clean, modular design.

REASONING: Analyzed project files and git commits
CONFIDENCE: 0.85"""

        else:
            # Generic helpful response
            return """I can help you with questions about your schedule, projects, communication patterns,
or manage tasks through my sub-agents like Mint (YouTube automation). What would you like to know?

REASONING: No specific context matched, providing general assistance
CONFIDENCE: 0.7"""

    def embed(self, text: str, dim: int = 384) -> List[float]:
        """
        Generate simple embedding for mock LLM

        Args:
            text: Input text
            dim: Embedding dimension

        Returns:
            Mock embedding vector
        """
        import hashlib

        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        embedding = []
        for i in range(dim):
            byte_val = hash_bytes[i % len(hash_bytes)]
            embedding.append((byte_val / 255.0) * 2.0 - 1.0)

        return embedding


# Alternative: Integration with other LLM providers

class OpenAILLM:
    """OpenAI API integration (optional)"""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(__name__)

    def generate(self, prompt: str, max_tokens: int = 500,
                temperature: float = 0.3) -> str:
        """Generate using OpenAI API"""
        try:
            import openai
            openai.api_key = self.api_key

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response.choices[0].message.content

        except ImportError:
            self.logger.error("openai package not installed")
            return "Error: OpenAI package not available"
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return f"Error: {str(e)}"


class AnthropicLLM:
    """Anthropic Claude API integration (optional)"""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key
        self.model = model
        self.logger = logging.getLogger(__name__)

    def generate(self, prompt: str, max_tokens: int = 500,
                temperature: float = 0.3) -> str:
        """Generate using Anthropic API"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except ImportError:
            self.logger.error("anthropic package not installed")
            return "Error: Anthropic package not available"
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            return f"Error: {str(e)}"
