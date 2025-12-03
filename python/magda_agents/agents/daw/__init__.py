"""
DAW Agent for MAGDA.

This module provides the DAW (Digital Audio Workstation) agent that translates
natural language to DAW actions using Grammar School DSL parsing.
"""

from magda_agents.agents.daw.daw_agent import DawAgent
from magda_agents.agents.daw.dsl_parser import DSLParser

__all__ = ["DawAgent", "DSLParser"]

