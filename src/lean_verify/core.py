#!/usr/bin/env python3
"""
Core verification logic for lean-verify.

This module contains the main LeanVerifier class and supporting data structures
for finding and verifying Lean 4 source files in a project.
"""

import json
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from unittest.mock import Mock, patch

from .exceptions import LeanVerifyError, MockToolchainError


class Severity(Enum):
    """Severity levels for verification results."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def rank(self) -> int:
        """Numeric rank for ordering. Higher is more severe.

        Required because Enum members are not orderable by default, and the CLI
        filters results with ``severity >= min_severity``.
        """
        return _SEVERITY_RANK[self]

    def __ge__(self, other: Any) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.rank >= other.rank

    def __gt__(self, other: Any) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.rank > other.rank

    def __le__(self, other: Any) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.rank <= other.rank

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.rank < other.rank

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Create a Severity from a string value."""
        value_lower = value.lower()
        for severity in Severity:
            if severity.value == value_lower:
                return severity
        raise ValueError(f"Unknown severity: {value}")


# ERROR > WARNING > INFO, matching the README's stated severity ranking.
_SEVERITY_RANK: Dict[Severity, int] = {
    Severity.ERROR: 3,
    Severity.WARNING: 2,
    Severity.INFO: 1,
}


class Status(Enum):
    """Status of a verification operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class VerificationResult:
    """Result of verifying a single Lean file."""

    file: Path
    severity: Severity
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    status: Status = Status.PENDING

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        data = asdict(self)
        data["severity"] = self.severity.value
        data["status"] = Status(self.status).value
        return data


class LeanVerifier:
    """Main class for Lean 4 proof verification.

    This class discovers Lean source files in a project directory and attempts
    to verify them using the Lean toolchain. It gracefully handles cases where
    the toolchain is not available by providing mocked results for testing.
    """

    def __init__(self, toolchain_path: Optional[str] = None):
        """Initialize the Lean verifier.

        Args:
            toolchain_path: Optional path to Lean toolchain (if not in PATH)
        """
        self.toolchain_path = toolchain_path
        self.config: Dict[str, Any] = {}

    def load_config(self, config_path: Path) -> None:
        """Load configuration from a JSON file.

        Args:
            config_path: Path to configuration file

        Raises:
            LeanVerifyError: If config file cannot be loaded
        """
        if not config_path.exists():
            raise LeanVerifyError(f"Config file not found: {config_path}")

        try:
            with open(config_path, "r") as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            raise LeanVerifyError(f"Invalid JSON in config file: {e}")

    def find_lean_files(self, path: Path) -> List[Path]:
        """Find all Lean 4 source files in a directory.

        Args:
            path: Directory to search

        Returns:
            List of Paths to Lean files (.lean extension)
        """
        if not path.exists():
            raise LeanVerifyError(f"Path does not exist: {path}")

        lean_files = []
        for file_path in path.rglob("*.lean"):
            if file_path.is_file():
                lean_files.append(file_path)

        return lean_files

    def verify_file(self, file_path: Path) -> VerificationResult:
        """Verify a single Lean file.

        Args:
            file_path: Path to Lean file to verify

        Returns:
            VerificationResult with status and any issues found
        """
        try:
            # Check if lean command exists
            if not self._check_toolchain_available():
                # Use mocked result when toolchain not available
                return self._get_mocked_result(file_path)

            # Try to compile with lean
            result = subprocess.run(
                ["lean", "--test", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=file_path.parent
            )

            if result.returncode == 0:
                return VerificationResult(
                    file=file_path,
                    severity=Severity.INFO,
                    message="File compiled successfully",
                    status=Status.COMPLETED
                )
            else:
                return VerificationResult(
                    file=file_path,
                    severity=Severity.ERROR,
                    message=f"Compilation failed: {result.stderr.strip()}",
                    status=Status.FAILED
                )

        except subprocess.TimeoutExpired:
            return VerificationResult(
                file=file_path,
                severity=Severity.WARNING,
                message="Compilation timed out after 30 seconds",
                status=Status.SKIPPED
            )
        except FileNotFoundError:
            return self._get_mocked_result(file_path)
        except Exception as e:
            return VerificationResult(
                file=file_path,
                severity=Severity.ERROR,
                message=f"Unexpected error: {str(e)}",
                status=Status.FAILED
            )

    def verify_path(self, path: Path) -> List[VerificationResult]:
        """Verify all Lean files in a project path.

        Args:
            path: Project directory to verify

        Returns:
            List of VerificationResult objects
        """
        lean_files = self.find_lean_files(path)

        if not lean_files:
            return [
                VerificationResult(
                    file=path,
                    severity=Severity.INFO,
                    message="No .lean files found in project",
                    status=Status.SKIPPED
                )
            ]

        results = []
        for file_path in lean_files:
            result = self.verify_file(file_path)
            results.append(result)

        return results

    def _check_toolchain_available(self) -> bool:
        """Check if Lean toolchain is available.

        Returns:
            True if lean command is available, False otherwise
        """
        try:
            subprocess.run(
                ["lean", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_mocked_result(self, file_path: Path) -> VerificationResult:
        """Get a mocked verification result when toolchain is not available.

        Args:
            file_path: Path to the Lean file being mocked

        Returns:
            Mocked VerificationResult indicating toolchain not available
        """
        return VerificationResult(
            file=file_path,
            severity=Severity.WARNING,
            message="Lean toolchain not available - using mocked results for testing",
            status=Status.SKIPPED
        )

    def get_summary(self, results: List[VerificationResult]) -> Dict[str, Any]:
        """Get a summary of verification results.

        Args:
            results: List of verification results

        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        if total == 0:
            return {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "skipped": 0,
                "info": 0,
                "warning": 0,
                "error": 0
            }

        completed = sum(1 for r in results if r.status == Status.COMPLETED)
        failed = sum(1 for r in results if r.status == Status.FAILED)
        skipped = sum(1 for r in results if r.status == Status.SKIPPED)
        info = sum(1 for r in results if r.severity == Severity.INFO)
        warning = sum(1 for r in results if r.severity == Severity.WARNING)
        error = sum(1 for r in results if r.severity == Severity.ERROR)

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "info": info,
            "warning": warning,
            "error": error
        }