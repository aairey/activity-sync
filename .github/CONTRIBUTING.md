# Contributing to Activity-Sync

Thank you for your interest in contributing to Activity-Sync! This document outlines the process for contributing to the project.

## Conventional Commits

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification. Please format your commit messages as follows:

```
<type>(<scope>): <description>
[optional body]
[optional footer(s)]
```

### Commit Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools and libraries
- `ci`: Changes to CI configuration files and scripts
- `build`: Changes that affect the build system or external dependencies

### Scopes

Scopes help define which part of the codebase the commit affects. Here are the available scopes for this project:

#### Core Functionality
- `sync`: Changes to the core synchronization logic
- `strava`: Strava API integration
- `nextcloud`: Nextcloud integration
- `gpx`: GPX file handling and processing
- `config`: Configuration management
- `state`: State management and persistence

#### Infrastructure
- `docker`: Docker-related changes
- `ci`: Continuous Integration configuration
- `deps`: Dependency updates
- `docs`: Documentation updates
- `tests`: Test-related changes

### Examples

```
feat(sync): add support for syncing new activity types
fix(strava): handle API rate limiting properly
docs: update README with new configuration options
refactor(config): simplify configuration loading
chore(deps): update aiohttp to v3.9.0
```

## Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes using the conventional commit format
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- Ruff for linting
- mypy for type checking

Please ensure your code passes all checks before submitting a PR.

## Testing

All new features and bug fixes should include appropriate tests. Run the test suite with:

```bash
pytest
```

## License

By contributing, you agree that your contributions will be licensed under the project's existing license.
