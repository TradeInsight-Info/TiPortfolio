# Contributing to TIPortfolio Project

- notebook dependency is not included in the pyproject.toml, please install it manually if you want to run the notebook examples.


## Report Structure
- TiPortfolio library [CLAUDE.md](src/tiportfolio/CLAUDE.md), a Python library and CLI tool for portfolio management and backtesting trading strategies, with built-in portfolio optimization algorithms.

- [notebooks](src/notebooks) directory with Jupyter notebooks demonstrating how to use the TiPortfolio library for various portfolio management tasks, including backtesting and optimization.


- [docs](docs) directory with documentation for the TiPortfolio library, including installation instructions, API reference, and usage examples. [openspec](openspec) directory with TiPortfolio specifications for design and implmentation details.





## TiPortfolio Structure

- Modular Architecture: The project is organized into distinct modules, each responsible for specific functionalities such as data handling, strategy implementation, risk management, and performance analysis.
- Simplicity: If a single file can effectively encapsulate a module's functionality without compromising clarity, we prefer that approach to maintain simplicity, fancy class or structure should be avoided unless necessary.
- Not reinventing the wheel: We leverage well-established libraries and frameworks to handle common tasks, allowing us to focus on the unique aspects of our project.

## Testing

We user pytest for testing. To run the tests, use the following command:

```bash
pytest tests/
```






## FAQ

### About AI and Vibe Coding
Vibe coding is accessible, however, to maintain quality and consistency, 
we have established some guidelines for contributions,

- Use AI tools as assistants, not primary authors.
- Know what you want to achieve before using AI tools.
- Always test and review AI-generated code thoroughly.
- Follow existing coding styles and project conventions.