# Contributing to TIPortfolio Project

- notebook dependency is not included in the pyproject.toml, please install it manually if you want to run the notebook examples.


## Commands

```bash
uv sync                        # install all dependencies
uv run python -m pytest                  # run all tests
uv run python -m pytest tests/file.py -v # run single file
uv run python -m pytest -k "pattern"     # run matching tests
uv run python -m mypy src/               # type check
uv run python -m black src/ tests/       # format
uv run python                  # always use uv run python, not python directly
```


## Structure

- src/tiportfolio/, the main library code.
- docs/, documentation for the library.
- tests/, unit tests with fixtures for offline testing.




## Testing

We user pytest for testing. To run the tests, use the following command:

```bash
uv run python -m pytest 
```


## FAQ

### About AI and Vibe Coding
Vibe coding is accessible, however, to maintain quality and consistency, 
we have established some guidelines for contributions,

- Use AI tools as assistants, not primary authors.
- Know what you want to achieve before using AI tools.
- Always test and review AI-generated code thoroughly.
- Follow existing coding styles and project conventions.