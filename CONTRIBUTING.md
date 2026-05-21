# Contributing to MiMo

Thank you for your interest in contributing to MiMo!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/<your-username>/mimo.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Set up the development environment (see below)

## Development Setup

```bash
# Install backend dependencies
cd backend && pip install -e ".[dev]"

# Install frontend dependencies
cd frontend && npm install

# Start infrastructure
make infra-up

# Start backend
make backend-dev

# Start frontend
make frontend-dev
```

## Code Standards

### Python (Backend)
- Python 3.9+ with `from __future__ import annotations`
- Use `Optional[X]` not `X | None`
- SQLAlchemy 2.0 declarative mapping (`Mapped[T]` + `mapped_column`)
- Pydantic v2 with `ConfigDict(from_attributes=True)`
- Linting: `ruff check app/`

### TypeScript (Frontend)
- Vue 3 Composition API with `<script setup lang="ts">`
- Element Plus for UI components
- Pinia for state management

## Testing

```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Frontend build check
cd frontend && npm run build
```

## Pull Request Process

1. Ensure all tests pass
2. Ensure `ruff check` passes with no errors
3. Update documentation if needed
4. Create a pull request with a clear description

## Reporting Issues

Use GitHub Issues to report bugs. Include:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details
