#!/usr/bin/env python3
"""
Exceptions module for lean-verify.

This module defines custom exceptions used throughout the lean-verify project
to handle various error conditions in a structured way.
"""


class LeanVerifyError(Exception):
    """Base exception for all lean-verify errors."""

    def __init__(self, message: str, cause: Exception = None):
        """Initialize a LeanVerifyError.

        Args:
            message: Human-readable error message
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


class MockToolchainError(LeanVerifyError):
    """Exception raised when mocked toolchain operations fail."""

    def __init__(self, message: str = "Mocked toolchain operation failed"):
        super().__init__(message)


class ConfigError(LeanVerifyError):
    """Exception raised when configuration is invalid."""

    def __init__(self, message: str, config_path: str = None):
        super().__init__(message)
        self.config_path = config_path

    def __str__(self) -> str:
        if self.config_path:
            return f"{self.message} (config: {self.config_path})"
        return self.message


class VerificationError(LeanVerifyError):
    """Exception raised during Lean verification operations."""

    def __init__(self, message: str, file_path: str = None, line: int = None):
        super().__init__(message)
        self.file_path = file_path
        self.line = line

    def __str__(self) -> str:
        if self.file_path:
            result = f"Error verifying {self.file_path}"
            if self.line:
                result += f" at line {self.line}"
            result += f": {self.message}"
            return result
        return self.message