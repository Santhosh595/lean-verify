# lean-verify — Lean 4 proof-verification harness CLI

[![CI](https://github.com/Santhosh595/lean-verify/actions/workflows/ci.yml/badge.svg)](https://github.com/Santhosh595/lean-verify/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Status:** Complete (GREENLIT by user 2026-08-26) → SLICE 1 ONLY

**Purpose:** Harness for reporting which Lean 4 theorems/definitions actually compile, severity-ranked per file, with --json output and CI exit codes. The "is the model's proof real?" checker.

**Toolchain constraints:**
- Stdlib-only orchestration wrapper
- Kernel (Lean/Lake) does the actual proof work
- NO Lean toolchain or elan install sanctioned per Tool Acquisition Policy
- Graceful "lean not found" degradation
- Test suite proves dispatch/parsing logic with MOCKED toolchain output

**Features:**
- Discovers `.lean` files in the project
- Invokes `lean/lake` IF present on system PATH
- Parses compile results with severity ranking
- JSON output (--json flag)
- Proper CI exit codes (0=success, >0=issues found)
- Mocked toolchain support for testing
- Extensible architecture for future Slice 2 real kernel support

**Installation:**
```bash
pip install -e .
```

**Usage:**
```bash
# Basic verification (finds .lean files and reports compilation status)
lean-verify

# JSON output for CI integration
lean-verify --json

# Exit code 0 if no issues, non-zero if problems found
lean-verify && echo "All proofs verified successfully"
```

**Testing:**
```bash
# Run unit tests (mocks toolchain)
pytest

# Run with verbose output
pytest -v
```

**Development notes:**
- Uses Python's `unittest.mock` for toolchain mocking in tests
- Supports both `lean` and `lake` commands
- Severity ranking: `error` > `warning` > `info`
- Mock fixture `mock_lean_output` available in tests
- No new external dependencies beyond Python stdlib

**Project structure:**
- `src/lean_verify/` – Main CLI implementation
- `tests/` – Unit tests with mocked toolchain
- `examples/` – Sample .lean files for testing
- `docs/` – Additional documentation

**Future Slice 2:**
- Real Lean toolchain support (requires user opt-in for elan installation)
- Enhanced error reporting and recovery
- Performance optimizations for large codebases