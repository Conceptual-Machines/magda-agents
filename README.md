# MAGDA Agents

Multi-language agent framework for MAGDA (Musical AI Digital Assistant).

## Overview

MAGDA Agents is the core framework that powers MAGDA's intelligent DAW control. It provides agents for:
- **DAW Agent**: Translates natural language to DAW actions
- **Plugin Agent**: Manages plugin discovery, deduplication, and alias generation
- **Arranger Agent**: Handles musical arrangement and composition

## Language Implementations

This framework is implemented in multiple languages. Each implementation provides the same core functionality:

### ⭐ Go Implementation (Production Ready)

**Repository:** [`magda-agents-go`](https://github.com/Conceptual-Machines/magda-agents-go)

```bash
go get github.com/Conceptual-Machines/magda-agents-go
```

```go
import (
    "github.com/Conceptual-Machines/magda-agents-go/agents/daw"
    "github.com/Conceptual-Machines/magda-agents-go/config"
)

agent := daw.NewDawAgent(cfg)
result, err := agent.GenerateActions(ctx, question, state)
```

### 🐍 Python Implementation

**Repository:** [`magda-agents-python`](https://github.com/Conceptual-Machines/magda-agents-python)

```bash
pip install magda-agents
```

```python
from magda_agents.agents.daw import DawAgent

agent = DawAgent(cfg)
result = agent.generate_actions(ctx, question, state)
```

## Features

- **Functional DSL Parser**: Supports `filter`, `map`, and `for_each` methods for collections
- **Grammar School Integration**: Built on [Grammar School](https://github.com/Conceptual-Machines/grammar-school) for LLM-friendly DSL parsing
- **Multiple LLM Providers**: OpenAI, Gemini support
- **Streaming Support**: Real-time action generation
- **REAPER Integration**: Direct translation to REAPER API actions

## Quick Links

- **Go**: [`magda-agents-go`](https://github.com/Conceptual-Machines/magda-agents-go) - Production-ready Go implementation
- **Python**: [`magda-agents-python`](https://github.com/Conceptual-Machines/magda-agents-python) - Python implementation
- **Documentation**: See individual language repositories for detailed docs
- **Grammar School**: [`grammar-school`](https://github.com/Conceptual-Machines/grammar-school) - DSL framework dependency

## Documentation

- [DAW Agent Documentation](https://github.com/Conceptual-Machines/magda-agents-go/tree/main/agents/daw)
- [DSL Grammar Reference](https://github.com/Conceptual-Machines/magda-agents-go/tree/main/llm)
- [Plugin Agent](https://github.com/Conceptual-Machines/magda-agents-go/tree/main/agents/plugin)
- [Arranger Agent](https://github.com/Conceptual-Machines/magda-agents-go/tree/main/agents/arranger)

## Contributing

Contributions welcome! Please see individual language repositories for contribution guidelines:
- [Go Contributing](https://github.com/Conceptual-Machines/magda-agents-go/blob/main/CONTRIBUTING.md)
- [Python Contributing](https://github.com/Conceptual-Machines/magda-agents-python/blob/main/CONTRIBUTING.md)

## License

AGPL v3 - See LICENSE file for details.
