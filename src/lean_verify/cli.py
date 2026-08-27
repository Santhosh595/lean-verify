#!/usr/bin/env python3
"""
CLI entry point for lean-verify.

This module provides the command-line interface for the Lean 4 proof-verification
harness, supporting JSON output, severity filtering, and proper exit codes.
"""

import argparse
import json
import sys
from pathlib import Path

from .core import LeanVerifier, Severity


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Lean 4 proof-verification harness",
        epilog="Used for CI integration and proof verification workflows."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON for CI integration"
    )
    parser.add_argument(
        "--min-severity",
        choices=["error", "warning", "info"],
        default="error",
        help="Minimum severity level to report (default: error)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file"
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Path to project directory (default: current directory)"
    )

    args = parser.parse_args()

    try:
        # Initialize the verifier
        verifier = LeanVerifier()

        # Load config if provided
        if args.config and args.config.exists():
            verifier.load_config(args.config)

        # Run verification
        results = verifier.verify_path(args.path)

        # Filter by severity if requested
        min_severity = Severity(args.min_severity)
        filtered_results = [
            r for r in results if r.severity >= min_severity
        ]

        if args.json:
            # JSON output for CI tools
            output = {
                "total_files": len(results),
                "verified_files": len(filtered_results),
                "results": [
                    {
                        "file": str(r.file),
                        "severity": r.severity.value,
                        "message": r.message,
                        "line": r.line,
                        "column": r.column,
                        "status": r.status.value
                    }
                    for r in filtered_results
                ]
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            print(f"Verifying project at: {args.path.absolute()}")
            print(f"Total files: {len(results)}")
            print(f"Verified files: {len(filtered_results)}")

            if filtered_results:
                print("\nIssues found:")
                for result in filtered_results:
                    print(f"  {result.severity.value.upper()}: {result.file}")
                    if result.line and result.column:
                        print(f"    Line {result.line}, Column {result.column}")
                    print(f"    {result.message}")
                    print()

        # Exit with appropriate code (0 if no issues, 1 if issues found)
        sys.exit(0 if len(filtered_results) == 0 else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()