"""
CFG (Context-Free Grammar) configuration for LLM providers.

This module provides utilities for working with CFG constraints
using Grammar School.
"""

from dataclasses import dataclass
from typing import Any

from grammar_school.openai_utils import OpenAICFG


@dataclass
class CFGConfig:
    """Configuration for Context-Free Grammar constraints."""

    tool_name: str  # Name of the tool that will receive the DSL output
    description: str  # Description of what the tool does
    grammar: str  # Lark or regex grammar definition
    syntax: str = "lark"  # "lark" or "regex" (default: "lark")

    def build_openai_tool(self) -> dict[str, Any]:
        """
        Build an OpenAI CFG tool payload using Grammar School.

        Returns:
            dict: OpenAI tool structure ready to be added to the tools array
        """
        cfg = OpenAICFG(
            tool_name=self.tool_name,
            description=self.description,
            grammar=self.grammar,
            syntax=self.syntax,
        )
        return cfg.build_tool()

    def get_openai_text_format(self) -> dict[str, Any]:
        """
        Get the text format configuration for OpenAI requests with CFG.

        Returns:
            dict: Text format config: {"format": {"type": "text"}}
        """
        cfg = OpenAICFG(
            tool_name=self.tool_name,
            description=self.description,
            grammar=self.grammar,
            syntax=self.syntax,
        )
        return cfg.get_text_format()

    def build_openai_request_config(self) -> dict[str, Any]:
        """
        Build a complete request configuration with both tool and text format.

        Returns:
            dict: Dict with "tool" and "text" keys ready for OpenAI request
        """
        cfg = OpenAICFG(
            tool_name=self.tool_name,
            description=self.description,
            grammar=self.grammar,
            syntax=self.syntax,
        )
        return cfg.build_request_config()

