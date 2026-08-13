# CV Platform

A computer vision platform runtime, registry, and execution environment.

## Directory Structure

```
CV-Platform/
├── docs/           # Documentation
├── spec/           # Specifications and schemas
├── runtime/        # Platform runtime configurations and state management
│   ├── registry/   # Registered modules and agents
│   ├── tasks/      # Task definitions and status
│   ├── locks/      # Lock files for concurrency
│   ├── agent-state/# State persistence for agents
│   ├── project.yaml# Runtime project configuration
│   └── state.yaml  # Runtime state definition
├── knowledge/      # Shared knowledge base
├── cv_platform/    # Main source package
├── tests/          # Tests suite
├── scripts/        # Automation and helper scripts
└── .github/        # CI/CD and workflows
```
