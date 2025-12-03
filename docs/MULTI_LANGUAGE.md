# Multi-Language Support

MAGDA Agents is designed as a multi-language framework, providing implementations in Go, Python, and TypeScript.

## Philosophy

The framework maintains **API parity** across all languages - the same functionality is available in each implementation, allowing developers to choose their preferred language.

## Language Implementations

### Go (`go/`)

**Status:** ✅ Production Ready

The primary implementation, used in the MAGDA API deployment.

**Features:**
- Full agent implementations
- LLM provider support (OpenAI, Gemini)
- DSL parser
- Complete test coverage

### Python (`python/`)

**Status:** 🚧 Under Development

**Planned Features:**
- Same agent interfaces as Go
- LLM provider support
- Pythonic API design
- Async/await support

### TypeScript (`typescript/`)

**Status:** 🚧 Under Development

**Planned Features:**
- Same agent interfaces as Go
- LLM provider support
- Type-safe API
- Node.js and browser support

## API Parity

All implementations provide the same core interfaces:

### DAW Agent

```go
// Go
agent := daw.NewDawAgent(cfg)
result, err := agent.GenerateActions(ctx, question, state)
```

```python
# Python (coming soon)
agent = DawAgent(cfg)
result = await agent.generate_actions(ctx, question, state)
```

```typescript
// TypeScript (coming soon)
const agent = new DawAgent(cfg);
const result = await agent.generateActions(ctx, question, state);
```

### Plugin Agent

```go
// Go
agent := plugin.NewPluginAgent(cfg)
aliases, err := agent.GenerateAliases(ctx, plugins)
```

```python
# Python (coming soon)
agent = PluginAgent(cfg)
aliases = await agent.generate_aliases(ctx, plugins)
```

```typescript
// TypeScript (coming soon)
const agent = new PluginAgent(cfg);
const aliases = await agent.generateAliases(ctx, plugins);
```

## Interface Contracts

All languages implement the same interface contracts:

- `AuthProvider` - Authentication abstraction
- `BillingProvider` - Billing/credits abstraction
- `DatabaseProvider` - Data persistence abstraction

## Contributing

When adding features:

1. **Implement in Go first** - Go is the reference implementation
2. **Document the interface** - Update this doc with examples
3. **Port to other languages** - Maintain API parity
4. **Update tests** - Ensure all languages have test coverage

## Language-Specific Considerations

### Go
- Uses interfaces for dependency injection
- Context-based cancellation
- Error handling with explicit returns

### Python
- Uses Protocol/ABC for interfaces
- Async/await for async operations
- Exception-based error handling

### TypeScript
- Uses interfaces/type aliases
- Promise-based async operations
- Type-safe error handling

## Roadmap

- [x] Go implementation (v1.0)
- [ ] Python implementation (v1.1)
- [ ] TypeScript implementation (v1.2)
- [ ] Cross-language examples
- [ ] Language-specific best practices guides

