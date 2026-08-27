# CONTRIBUTING.md

This file provides guidelines for contributing to lean-verify.

## Project Structure

```
lean-verify/
├── src/
│   └── lean_verify/              # Core package
│       ├── __init__.py          # Package exports
│       ├── cli.py               # Command-line interface
│       ├── core.py              # Main verification logic
│       └── exceptions.py        # Custom exceptions
├── tests/                       # Test suite
│   └── test_lean_verify.py      # Unit tests
├── examples/                    # Example Lean files
│   └── example1.lean            # Sample Lean file
├── docs/                        # Documentation
└── README.md                    # Project documentation
```

## Development Workflow

1. **Environment Setup**
   - Install dependencies: `pip install -e .`
   - Install testing framework: `pip install pytest`

2. **Running Tests**
   ```bash
   pytest
   pytest -v
   ```

3. **Code Quality**
   - Follow PEP 8 style guidelines
   - Write comprehensive tests
   - Use type hints where appropriate

4. **Version Control**
   - Use conventional commit messages
   - Branch naming: `feat/<feature-name>` or `fix/<issue-name>`
   - Prefix feature branches with `feat/` or `fix/`

## Testing Guidelines

### Test Coverage
- Unit tests for all core functionality
- Mock toolchain for testing when Lean is not available
- Comprehensive error handling tests

### Test Structure
- Each test class focuses on a specific component
- Tests use pytest fixtures for setup
- Mock subprocess calls for toolchain testing
- Edge cases and error conditions are tested

## Building and Distribution

### Installation
```bash
pip install -e .
```

### Running the CLI
```bash
lean-verify                    # Basic verification
lean-verify --json             # JSON output
lean-verify --min-severity warning  # Filter by severity
lean-verify --config config.json  # Load configuration
```

### Usage Examples

Basic verification:
```bash
# Verify all Lean files in current directory
lean-verify

# Output in JSON format for CI integration
lean-verify --json

# Filter by severity (show only errors and warnings)
lean-verify --min-severity warning
```

Configuration:
```bash
# Create a config file
cat > config.json << EOF
{
  "max_files": 100,
  "output_format": "json",
  "severity_filter": "error"
}
EOF

# Use config file
lean-verify --config config.json
```

## Code Standards

### Python Standards
- **Style**: PEP 8 compliant
- **Type Hints**: Use type annotations
- **Docstrings**: Google style format
- **Testing**: pytest with comprehensive coverage

### File Organization
- `src/lean_verify/` for production code
- `tests/` for test files
- `examples/` for example files
- `docs/` for additional documentation

### Error Handling
- Use custom exceptions for specific error types
- Graceful degradation when toolchain is not available
- Clear error messages for debugging

## Troubleshooting

### Common Issues

1. **Lean Toolchain Not Available**
   - The tool gracefully handles missing Lean toolchain
   - Uses mocked results for testing purposes
   - No installation required for basic functionality

2. **Test Failures**
   - Ensure all dependencies are installed
   - Run tests with verbose output for details
   - Check for any mocking issues in test files

3. **Import Errors**
   - Install the package in development mode: `pip install -e .`
   - Ensure all Python dependencies are available

## Future Development

### Planned Features
1. **Slice 2 Implementation**
   - Real Lean toolchain support
   - Enhanced error reporting
   - Performance optimizations

2. **Additional Features**
   - Support for multiple Lean versions
   - Integration with CI/CD pipelines
   - Extended configuration options

### Known Limitations
- Requires Lean toolchain for actual verification
- Limited to .lean files only
- Basic error reporting without detailed diagnostics

## License

This project is licensed under the MIT License.

See LICENSE for more information.

## Acknowledgments

Special thanks to the Lean 4 community for providing an excellent theorem prover!
