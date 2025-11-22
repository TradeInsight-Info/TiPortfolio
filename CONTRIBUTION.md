# Contributing to TIPortfolio Project

- notebook dependency is not included in the pyproject.toml, please install it manually if you want to run the notebook examples.

## Structure

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