# lean-verify - Lean 4 proof-verification harness CLI
# Copyright (c) 2026 Santhosh595
# SPDX-License-Identifier: MIT

"""
Harness for reporting which Lean 4 theorems/definitions actually compile,
severity-ranked per file, with --json output and CI exit codes.

The "is the model's proof real?" checker.

This is a stdlib-only orchestration wrapper. The kernel (Lean/Lake) does the
actual proof work. This implementation gracefully degrades when the Lean
toolchain is not available and uses mocked toolchain output for testing.
"""

__version__ = "0.1.0"
__author__ = "Santhosh595"

from .cli import main
from .core import LeanVerifier, VerificationResult, Severity
from .exceptions import LeanVerifyError

__all__ = [
    "main",
    "LeanVerifier", 
    "VerificationResult",
    "Severity",
    "LeanVerifyError"
]