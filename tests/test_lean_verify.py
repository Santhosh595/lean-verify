#!/usr/bin/env python3
"""
Test suite for lean-verify.

This module contains unit tests for the lean-verify project, using mocked
toolchain output to avoid requiring the actual Lean toolchain installation.
"""

import json
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from lean_verify.core import LeanVerifier, VerificationResult, Severity, Status
from lean_verify.exceptions import LeanVerifyError, MockToolchainError, ConfigError, VerificationError


class TestSeverity:
    """Test Severity enum functionality."""

    def test_severity_from_string(self):
        """Test Severity.from_string method."""
        assert Severity.from_string("error") == Severity.ERROR
        assert Severity.from_string("warning") == Severity.WARNING
        assert Severity.from_string("info") == Severity.INFO

    def test_severity_from_string_invalid(self):
        """Test Severity.from_string with invalid input."""
        with pytest.raises(ValueError):
            Severity.from_string("invalid")

    def test_severity_values(self):
        """Test severity enum values."""
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"


class TestVerificationResult:
    """Test VerificationResult dataclass."""

    def test_verification_result_creation(self):
        """Test basic VerificationResult creation."""
        result = VerificationResult(
            file=Path("/test/example.lean"),
            severity=Severity.ERROR,
            message="Test error",
            line=10,
            column=5,
            status=Status.FAILED
        )

        assert result.file == Path("/test/example.lean")
        assert result.severity == Severity.ERROR
        assert result.message == "Test error"
        assert result.line == 10
        assert result.column == 5
        assert result.status == Status.FAILED

    def test_verification_result_to_dict(self):
        """Test VerificationResult.to_dict method."""
        result = VerificationResult(
            file=Path("/test/example.lean"),
            severity=Severity.WARNING,
            message="Test warning",
            line=20,
            status=Status.COMPLETED
        )

        result_dict = result.to_dict()
        assert result_dict["file"] == Path("/test/example.lean")
        assert result_dict["severity"] == "warning"
        assert result_dict["message"] == "Test warning"
        assert result_dict["line"] == 20
        assert result_dict["status"] == "completed"

    def test_verification_result_default_values(self):
        """Test VerificationResult with default values."""
        result = VerificationResult(
            file=Path("/test/example.lean"),
            severity=Severity.INFO,
            message="Test info"
        )

        assert result.line is None
        assert result.column is None
        assert result.status == Status.PENDING


class TestLeanVerifier:
    """Test LeanVerifier class."""

    @pytest.fixture
    def verifier(self):
        """Fixture for LeanVerifier instance."""
        return LeanVerifier()

    def test_init(self, verifier):
        """Test LeanVerifier initialization."""
        assert verifier.toolchain_path is None
        assert verifier.config == {}

    def test_init_with_toolchain_path(self):
        """Test LeanVerifier initialization with toolchain path."""
        verifier = LeanVerifier("/path/to/lean")
        assert verifier.toolchain_path == "/path/to/lean"

    def test_find_lean_files(self, verifier):
        """Test finding Lean files in a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test .lean files
            (temp_path / "test1.lean").write_text("def foo := 1")
            (temp_path / "test2.lean").write_text("def bar := 2")
            (temp_path / "not_lean.txt").write_text("Not a lean file")

            # Create subdirectory with lean file
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "subfile.lean").write_text("def baz := 3")

            # Find lean files
            lean_files = verifier.find_lean_files(temp_path)

            expected_files = [
                temp_path / "test1.lean",
                temp_path / "test2.lean",
                subdir / "subfile.lean"
            ]

            assert len(lean_files) == 3
            for expected_file in expected_files:
                assert expected_file in lean_files

    def test_find_lean_files_nonexistent_path(self, verifier):
        """Test finding Lean files in non-existent path."""
        with pytest.raises(LeanVerifyError, match="Path does not exist"):
            verifier.find_lean_files(Path("/nonexistent/path"))

    def test_check_toolchain_available(self, verifier):
        """Test toolchain availability check."""
        # Mock subprocess.run to simulate lean command being available
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Lean version 3.42.0"

            assert verifier._check_toolchain_available() == True

    def test_check_toolchain_not_available(self, verifier):
        """Test toolchain availability when command not found."""
        # Mock subprocess.run to simulate FileNotFoundError
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError

            assert verifier._check_toolchain_available() == False

    def test_verify_file_with_mocked_toolchain(self, verifier):
        """Test verify_file when toolchain is mocked."""
        with patch.object(verifier, "_check_toolchain_available", return_value=False):
            result = verifier.verify_file(Path("/test/example.lean"))

            assert result.file == Path("/test/example.lean")
            assert result.severity == Severity.WARNING
            assert "not available" in result.message
            assert result.status == Status.SKIPPED

    def test_verify_file_compilation_success(self, verifier):
        """Test verify_file with successful compilation."""
        with patch.object(verifier, "_check_toolchain_available", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "OK"
                mock_run.return_value.stderr = ""

                result = verifier.verify_file(Path("/test/example.lean"))

                assert result.file == Path("/test/example.lean")
                assert result.severity == Severity.INFO
                assert result.message == "File compiled successfully"
                assert result.status == Status.COMPLETED

    def test_verify_file_compilation_failure(self, verifier):
        """Test verify_file with compilation failure."""
        with patch.object(verifier, "_check_toolchain_available", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stdout = ""
                mock_run.return_value.stderr = "Error: undefined variable"

                result = verifier.verify_file(Path("/test/example.lean"))

                assert result.file == Path("/test/example.lean")
                assert result.severity == Severity.ERROR
                assert "Compilation failed" in result.message
                assert result.status == Status.FAILED

    def test_verify_file_timeout(self, verifier):
        """Test verify_file with timeout."""
        with patch.object(verifier, "_check_toolchain_available", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("lean", 30)

                result = verifier.verify_file(Path("/test/example.lean"))

                assert result.file == Path("/test/example.lean")
                assert result.severity == Severity.WARNING
                assert "timed out" in result.message
                assert result.status == Status.SKIPPED

    def test_verify_file_exception(self, verifier):
        """Test verify_file with unexpected exception."""
        with patch.object(verifier, "_check_toolchain_available", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = Exception("Unexpected error")

                result = verifier.verify_file(Path("/test/example.lean"))

                assert result.file == Path("/test/example.lean")
                assert result.severity == Severity.ERROR
                assert "Unexpected error" in result.message
                assert result.status == Status.FAILED

    def test_verify_path_with_mocked_toolchain(self, verifier):
        """Test verify_path when toolchain is mocked."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test .lean files
            (temp_path / "test1.lean").write_text("def foo := 1")
            (temp_path / "test2.lean").write_text("def bar := 2")

            with patch.object(verifier, "_check_toolchain_available", return_value=False):
                results = verifier.verify_path(temp_path)

                assert len(results) == 2
                for result in results:
                    assert result.severity == Severity.WARNING
                    assert result.status == Status.SKIPPED

    def test_verify_path_no_lean_files(self, verifier):
        """Test verify_path when no .lean files found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create no .lean files, only other files
            (temp_path / "README.md").write_text("# Test Project")

            results = verifier.verify_path(temp_path)

            assert len(results) == 1
            assert results[0].severity == Severity.INFO
            assert "No .lean files found" in results[0].message
            assert results[0].status == Status.SKIPPED

    def test_load_config(self, verifier):
        """Test loading configuration from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"max_files": 100, "output_format": "json"}, f)
            config_path = Path(f.name)

        try:
            verifier.load_config(config_path)
            assert verifier.config == {"max_files": 100, "output_format": "json"}
        finally:
            config_path.unlink()

    def test_load_config_file_not_found(self, verifier):
        """Test loading configuration from non-existent file."""
        with pytest.raises(LeanVerifyError, match="Config file not found"):
            verifier.load_config(Path("/nonexistent/config.json"))

    def test_load_config_invalid_json(self, verifier):
        """Test loading configuration with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            config_path = Path(f.name)

        try:
            with pytest.raises(LeanVerifyError, match="Invalid JSON"):
                verifier.load_config(config_path)
        finally:
            config_path.unlink()

    def test_get_summary(self, verifier):
        """Test getting summary statistics from results."""
        results = [
            VerificationResult(Path("test1.lean"), Severity.INFO, "Info", status=Status.COMPLETED),
            VerificationResult(Path("test2.lean"), Severity.WARNING, "Warning", status=Status.SKIPPED),
            VerificationResult(Path("test3.lean"), Severity.ERROR, "Error", status=Status.FAILED),
        ]

        summary = verifier.get_summary(results)

        assert summary["total"] == 3
        assert summary["completed"] == 1
        assert summary["skipped"] == 1
        assert summary["failed"] == 1
        assert summary["info"] == 1
        assert summary["warning"] == 1
        assert summary["error"] == 1

    def test_get_summary_empty(self, verifier):
        """Test getting summary statistics from empty results."""
        summary = verifier.get_summary([])

        assert summary["total"] == 0
        assert summary["completed"] == 0
        assert summary["failed"] == 0
        assert summary["skipped"] == 0
        assert summary["info"] == 0
        assert summary["warning"] == 0
        assert summary["error"] == 0


class TestExceptionClasses:
    """Test custom exception classes."""

    def test_lean_verify_error(self):
        """Test LeanVerifyError."""
        error = LeanVerifyError("Test error")
        assert str(error) == "Test error"

        error_with_cause = LeanVerifyError("Test error", ValueError("cause"))
        assert "caused by" in str(error_with_cause).lower()

    def test_mock_toolchain_error(self):
        """Test MockToolchainError."""
        error = MockToolchainError()
        assert "Mocked toolchain operation failed" in str(error)

        error_custom = MockToolchainError("Custom message")
        assert "Custom message" in str(error_custom)

    def test_config_error(self):
        """Test ConfigError."""
        error = ConfigError("Invalid config")
        assert str(error) == "Invalid config"

        error_with_path = ConfigError("Invalid config", "/path/to/config.json")
        assert "/path/to/config.json" in str(error_with_path)

    def test_verification_error(self):
        """Test VerificationError."""
        error = VerificationError("Verification failed")
        assert str(error) == "Verification failed"

        error_with_details = VerificationError(
            "Verification failed", 
            "/test/file.lean", 
            line=42
        )
        assert "/test/file.lean" in str(error_with_details)
        assert "line 42" in str(error_with_details)