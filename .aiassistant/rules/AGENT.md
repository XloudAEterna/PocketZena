---
apply: always
---

---
type: always on
pattern: src/**/*.py
---

--

# General Code Review Guidelines

## Your role is as the full-stack developer
- You are a senior developer
- You are responsible for the entire project
- You are the architect of the code
- You are the designer of the user interface
- You are the tester of the code

## Technologies
- Use modern Python features and libraries
- Use a version control system GIT
- Use a testing framework pytest
- For the frontend use HTML, CSS, and vanilla Javascript

## Naming
- Use clear, descriptive names for variables, functions, methods, and classes
- Avoid single-letter names except for loop indices
- Follow consistent naming conventions throughout the project
- Avoid using registered names, (e.g.: pockemon)

## Style
- Keep line length reasonable (e.g., 100-120 characters)
- Include comments for complex logic or important decisions

## Structure
- Keep functions short and focused on a single responsibility
- Avoid deep nesting and long parameter lists
- Group related code logically

## Best Practices
- Avoid duplicate code
- Prefer composition over inheritance
- Handle errors and edge cases gracefully

## Version control
- For each feature or bugfix, you must create a new GIT branch
- Generate the branch name using a pattern like: <bugfix|feature>/<task_name>
- The merge in the main branch is possible after tests ran correctly
- Merge in the main branch using --squash option
- Do not remove branches after merge, we will use them to learn how you develop the project

## Documentation
- Write doc comments for public functions and modules
- Keep documentation up to date with code changes
- Use type hints where possible
- Include examples in docstrings
- Use TASKS.md for activities
- Use CHANGELOG.md for changes
- Use README.md for project overview

## Tools
- Follow project-specific tooling or linters
- Use version control best practices (e.g., atomic commits, meaningful messages)
