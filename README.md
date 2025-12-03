# MAGDA Agents

Multi-language agent framework for MAGDA (Musical AI Digital Assistant).

## Overview

MAGDA Agents is the core framework that powers MAGDA's intelligent DAW control. It provides agents for:
- **DAW Agent**: Translates natural language to DAW actions
- **Plugin Agent**: Manages plugin discovery, deduplication, and alias generation
- **Arranger Agent**: Handles musical arrangement and composition

## Multi-Language Support

This framework is designed to be language-agnostic and provides implementations in:

- **Go** (`go/`) - Primary implementation, production-ready
- **Python** (`python/`) - Coming soon
- **TypeScript** (`typescript/`) - Coming soon

Each language implementation provides the same core functionality and interfaces, allowing you to use MAGDA Agents in your preferred language.

## Architecture

```
magda-agents/
├── go/              # Go implementation
├── python/           # Python implementation (scaffolding)
├── typescript/       # TypeScript implementation (scaffolding)
└── docs/             # Shared documentation
```

## Quick Start

### Go

```go
import (
    "github.com/conceptual-machines/magda-agents/go/agents/daw"
)

agent := daw.NewDawAgent(cfg)
result, err := agent.GenerateActions(ctx, question, state)
```

### Python (Coming Soon)

```python
from magda_agents.agents.daw import DawAgent

agent = DawAgent(cfg)
result = agent.generate_actions(ctx, question, state)
```

### TypeScript (Coming Soon)

```typescript
import { DawAgent } from '@conceptual-machines/magda-agents';

const agent = new DawAgent(cfg);
const result = await agent.generateActions(ctx, question, state);
```

## Installation

### Go

```bash
go get github.com/conceptual-machines/magda-agents/go/agents/daw
```

### Python (Coming Soon)

```bash
pip install magda-agents
```

### TypeScript (Coming Soon)

```bash
npm install @conceptual-machines/magda-agents
```

## License

AGPL v3 - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Agent Interfaces](docs/INTERFACES.md)
- [Multi-Language Guide](docs/MULTI_LANGUAGE.md)

