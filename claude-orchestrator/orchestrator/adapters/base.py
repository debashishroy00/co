"""
Base adapter interface for language-specific orchestrator behavior.
"""
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path


class BaseAdapter(ABC):
    """Base class for language-specific adapters."""

    @property
    @abstractmethod
    def language(self) -> str:
        """Return the language name this adapter handles."""
        pass

    @property
    @abstractmethod
    def default_tools(self) -> Dict[str, str]:
        """Return default tool commands for this language."""
        pass

    @property
    @abstractmethod
    def default_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Return default metrics configuration for this language."""
        pass

    def test_tool(self, command: str) -> bool:
        """Test if a tool command is available and working."""
        try:
            # Split command and take first part (tool name)
            tool_parts = command.split()
            if not tool_parts:
                return False

            tool_name = tool_parts[0]

            # Test if tool exists
            result = subprocess.run(
                [tool_name, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False

    def run_command(self, command: str, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        return subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=300  # 5 minute timeout
        )

    def parse_test_output(self, output: str) -> Dict[str, Any]:
        """Parse test output to extract metrics."""
        # Default implementation - subclasses should override
        lines = output.split('\n')

        # Look for common patterns
        passed = sum(1 for line in lines if 'PASSED' in line or 'PASS' in line or '✓' in line)
        failed = sum(1 for line in lines if 'FAILED' in line or 'FAIL' in line or '✗' in line)

        return {
            "passed": passed,
            "failed": failed,
            "total": passed + failed,
            "success": failed == 0
        }

    def parse_lint_output(self, output: str) -> Dict[str, Any]:
        """Parse lint output to extract issues."""
        # Default implementation
        lines = output.split('\n')

        errors = sum(1 for line in lines if 'error' in line.lower())
        warnings = sum(1 for line in lines if 'warning' in line.lower())

        return {
            "errors": errors,
            "warnings": warnings,
            "total_issues": errors + warnings,
            "success": errors == 0
        }

    def parse_security_output(self, output: str) -> Dict[str, Any]:
        """Parse security scan output to extract findings."""
        # Default implementation
        lines = output.split('\n')

        high = sum(1 for line in lines if 'high' in line.lower() and ('severity' in line.lower() or 'risk' in line.lower()))
        medium = sum(1 for line in lines if 'medium' in line.lower() and ('severity' in line.lower() or 'risk' in line.lower()))
        low = sum(1 for line in lines if 'low' in line.lower() and ('severity' in line.lower() or 'risk' in line.lower()))

        return {
            "high": high,
            "medium": medium,
            "low": low,
            "total_issues": high + medium + low,
            "success": high == 0
        }

    def extract_coverage(self, output: str) -> Optional[float]:
        """Extract test coverage percentage from output."""
        import re

        # Look for patterns like "85%" or "85.5%"
        coverage_patterns = [
            r'TOTAL.*?(\d+(?:\.\d+)?)%',  # pytest-cov format
            r'coverage:\s*(\d+(?:\.\d+)?)%',  # generic coverage
            r'(\d+(?:\.\d+)?)%\s*coverage',  # alternative format
        ]

        for pattern in coverage_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def get_project_files(self, project_path: Path) -> List[Path]:
        """Get list of source files for this language."""
        # Default implementation - subclasses should override with language-specific extensions
        return list(project_path.rglob("*"))

    def estimate_complexity(self, file_path: Path) -> int:
        """Estimate code complexity (e.g., cyclomatic complexity)."""
        try:
            content = file_path.read_text()
            lines = content.split('\n')

            # Simple complexity estimation based on control flow keywords
            complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'switch', 'case']
            complexity = 1  # Base complexity

            for line in lines:
                for keyword in complexity_keywords:
                    if keyword in line:
                        complexity += 1

            return complexity
        except Exception:
            return 0

    def get_function_count(self, file_path: Path) -> int:
        """Count number of functions in a file."""
        try:
            content = file_path.read_text()
            lines = content.split('\n')

            # Generic function detection - subclasses should override
            function_count = 0
            for line in lines:
                if any(keyword in line for keyword in ['def ', 'function ', 'func ']):
                    function_count += 1

            return function_count
        except Exception:
            return 0

    def validate_function_length(self, file_path: Path, max_lines: int = 30) -> List[str]:
        """Check if functions exceed maximum line limit."""
        # Default implementation - subclasses should implement language-specific parsing
        violations = []

        try:
            content = file_path.read_text()
            lines = content.split('\n')

            current_function = None
            function_start = 0

            for i, line in enumerate(lines):
                # Simple function detection - override in subclasses
                if 'def ' in line or 'function ' in line:
                    if current_function and (i - function_start) > max_lines:
                        violations.append(f"{current_function} exceeds {max_lines} lines ({i - function_start} lines)")

                    current_function = line.strip()
                    function_start = i

            # Check last function
            if current_function and (len(lines) - function_start) > max_lines:
                violations.append(f"{current_function} exceeds {max_lines} lines ({len(lines) - function_start} lines)")

        except Exception:
            pass

        return violations

    def format_code(self, file_path: Path) -> bool:
        """Format code using language-specific formatter."""
        # Default implementation - subclasses should override
        return True

    def get_dependencies(self, project_path: Path) -> List[str]:
        """Get list of project dependencies."""
        # Default implementation - subclasses should override
        return []

    def check_security_patterns(self, content: str) -> List[Dict[str, str]]:
        """Check for common security anti-patterns in code."""
        import re

        issues = []

        # Generic security patterns
        patterns = {
            "hardcoded_secret": r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']',
            "sql_injection": r'(SELECT|INSERT|UPDATE|DELETE).*\+.*',
            "command_injection": r'(exec|eval|system)\s*\(',
            "path_traversal": r'\.\./|\.\.\\'
        }

        for issue_type, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": issue_type,
                    "pattern": match.group(),
                    "severity": "high" if issue_type in ["command_injection", "sql_injection"] else "medium"
                })

        return issues