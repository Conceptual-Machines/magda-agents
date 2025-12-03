"""
LLM provider interface and types for MAGDA Agents.

This module defines the provider interface and request/response types
used across all LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from magda_agents.llm.cfg_config import CFGConfig


@dataclass
class OutputSchema:
    """Defines the expected JSON output structure."""

    name: str
    description: str
    schema: dict[str, Any]  # JSON Schema object


@dataclass
class GenerationRequest:
    """Request parameters for LLM generation."""

    model: str
    input_array: list[dict[str, Any]]
    reasoning_mode: str = ""
    system_prompt: str = ""
    output_schema: OutputSchema | None = None
    cfg_grammar: CFGConfig | None = None


@dataclass
class Usage:
    """Token usage information from LLM response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class GenerationResponse:
    """Response from LLM generation."""

    raw_output: str  # Raw text/DSL output from the model
    usage: Usage | None = None
    parsed_output: Any = None  # Parsed output (if applicable)


class Provider(ABC):
    """
    Base interface for LLM providers.

    All providers MUST support structured output (JSON Schema) or
    CFG grammar constraints for reliable response parsing.
    """

    @abstractmethod
    def generate(
        self, request: GenerationRequest
    ) -> GenerationResponse:
        """
        Generate a response using the LLM.

        Args:
            request: Generation request with model, prompt, and output constraints

        Returns:
            GenerationResponse: The generated response with raw and parsed output

        Raises:
            ProviderError: If generation fails
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """
        Return the provider name (e.g., "openai", "gemini").

        Returns:
            str: Provider name
        """
        pass

