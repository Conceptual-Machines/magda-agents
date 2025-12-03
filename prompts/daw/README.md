# DAW Agent Prompts

This directory contains prompts for the DAW (Digital Audio Workstation) agent.

## Files

- `system_prompt.txt` - Main system prompt for the DAW agent

## Usage

These prompts are language-agnostic and can be loaded by any implementation (Go, Python, TypeScript).

## Note on MCP

The original prompts included references to MCP (Model Context Protocol) tools for accessing a music theory database. These have been removed from the open source version as:
1. MCP integration is deployment-specific
2. The music theory database is proprietary
3. The framework should be decoupled from specific data sources

Deployment-specific implementations (like `magda-api`) can extend these prompts with MCP references if needed.

