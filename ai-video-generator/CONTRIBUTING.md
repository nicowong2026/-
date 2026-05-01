# Contributing to AI Video Generator

Thank you for your interest in contributing! 🎉

## Getting Started

```bash
git clone https://github.com/your-username/ai-video-generator.git
cd ai-video-generator
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Development Workflow

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feat/your-feature` or `fix/your-bug`
3. **Write code** following the style guide below
4. **Add tests** for any new functionality
5. **Run the test suite**: `pytest tests/ -v`
6. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/)
7. **Push** and open a **Pull Request**

## Commit Convention

```
feat: add Pika Labs video backend
fix: handle empty script edge case in agent
docs: update API reference for new endpoints
test: add coverage for subtitle embedder
refactor: extract common retry logic to utils
chore: bump dependencies
```

## Code Style

- **Formatter**: `black` (line length 88)
- **Linter**: `ruff`
- **Type hints**: Required for all public functions
- **Docstrings**: Google style

```bash
black src/ tests/
ruff check --fix src/ tests/
mypy src/
```

## Adding a New Backend

1. Add the backend class in the appropriate `src/generators/` file
2. Update the `Backend` type alias
3. Implement the private `_generate_<backend>` method
4. Add an entry in `README.md` under "Supported AI Models"
5. Add tests in `tests/`

## Pull Request Checklist

- [ ] Tests pass (`pytest tests/`)
- [ ] No linting errors (`ruff check src/`)
- [ ] Type-checked (`mypy src/`)
- [ ] Docs updated (if applicable)
- [ ] Changelog entry added

## Questions?

Open a [Discussion](https://github.com/your-username/ai-video-generator/discussions) — we're happy to help!
