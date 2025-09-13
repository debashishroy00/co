"""
Python-specific adapter for the Claude Code Orchestrator.
Handles Python projects with support for various frameworks and tools.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import BaseAdapter


class PythonAdapter(BaseAdapter):
    """Adapter for Python projects."""

    @property
    def language(self) -> str:
        return "python"

    @property
    def default_tools(self) -> Dict[str, str]:
        return {
            "test": "pytest --cov=. tests/",
            "lint": "ruff check .",
            "format": "ruff format .",
            "typecheck": "mypy .",
            "security": "bandit -r . -f json",
            "dependencies": "safety check"
        }

    @property
    def default_metrics(self) -> Dict[str, Dict[str, Any]]:
        return {
            "performance": {
                "execution_time": {"target": -5, "cap": 15, "unit": "%"},
                "memory_usage": {"target": 0, "cap": 20, "unit": "%"},
                "import_time": {"target": -10, "cap": 10, "unit": "%"}
            },
            "quality": {
                "test_coverage": {"target": 80, "absolute": True, "unit": "%"},
                "cyclomatic_complexity": {"target": 10, "absolute": True, "unit": "max"},
                "maintainability_index": {"target": 70, "absolute": True, "unit": "score"}
            },
            "security": {
                "bandit_issues": {"target": 0, "absolute": True, "unit": "count"},
                "dependency_vulnerabilities": {"target": 0, "absolute": True, "unit": "count"}
            }
        }

    def parse_test_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract detailed metrics."""
        lines = output.split('\n')

        # Parse pytest results
        passed = 0
        failed = 0
        skipped = 0
        coverage = None

        for line in lines:
            # Count test results
            if ' PASSED' in line or '::' in line and 'PASSED' in line:
                passed += 1
            elif ' FAILED' in line or '::' in line and 'FAILED' in line:
                failed += 1
            elif ' SKIPPED' in line or '::' in line and 'SKIPPED' in line:
                skipped += 1

            # Extract coverage
            if 'TOTAL' in line and '%' in line:
                coverage_match = re.search(r'(\d+)%', line)
                if coverage_match:
                    coverage = int(coverage_match.group(1))

        # Look for summary line
        summary_pattern = r'=+\s*(\d+)\s+failed.*?(\d+)\s+passed.*?in\s+([\d.]+)s'
        summary_match = re.search(summary_pattern, output)
        if summary_match:
            failed = int(summary_match.group(1))
            passed = int(summary_match.group(2))

        return {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": passed + failed + skipped,
            "coverage": coverage,
            "success": failed == 0,
            "status": "PASS" if failed == 0 else "FAIL"
        }

    def parse_lint_output(self, output: str) -> Dict[str, Any]:
        """Parse ruff output to extract issues."""
        lines = output.split('\n')

        errors = 0
        warnings = 0
        issues_by_type = {}

        for line in lines:
            # Ruff format: file:line:col: CODE message
            if ':' in line and re.search(r'[A-Z]\d{3}', line):
                # Extract error code
                code_match = re.search(r'([A-Z]\d{3})', line)
                if code_match:
                    code = code_match.group(1)
                    issues_by_type[code] = issues_by_type.get(code, 0) + 1

                    # Categorize as error or warning based on code
                    if code.startswith(('E', 'F')):  # Error, Fatal
                        errors += 1
                    else:
                        warnings += 1

        return {
            "errors": errors,
            "warnings": warnings,
            "total_issues": errors + warnings,
            "issues_by_type": issues_by_type,
            "success": errors == 0,
            "status": "PASS" if errors == 0 else "ISSUES"
        }

    def parse_security_output(self, output: str) -> Dict[str, Any]:
        """Parse bandit JSON output to extract security findings."""
        try:
            # Try to parse as JSON first
            bandit_data = json.loads(output)

            metrics = bandit_data.get('metrics', {})
            totals = metrics.get('_totals', {})

            high = totals.get('SEVERITY.HIGH', 0)
            medium = totals.get('SEVERITY.MEDIUM', 0)
            low = totals.get('SEVERITY.LOW', 0)

            results = bandit_data.get('results', [])
            issues_by_type = {}

            for result in results:
                test_id = result.get('test_id', 'unknown')
                issues_by_type[test_id] = issues_by_type.get(test_id, 0) + 1

            return {
                "high": high,
                "medium": medium,
                "low": low,
                "total_issues": high + medium + low,
                "issues_by_type": issues_by_type,
                "success": high == 0,
                "status": "CLEAR" if high == 0 else "ISSUES"
            }

        except json.JSONDecodeError:
            # Fallback to text parsing
            return super().parse_security_output(output)

    def get_project_files(self, project_path: Path) -> List[Path]:
        """Get Python source files."""
        python_files = []

        # Include common Python file patterns
        patterns = ["*.py", "*.pyx", "*.pyi"]

        for pattern in patterns:
            python_files.extend(project_path.rglob(pattern))

        # Filter out common ignore patterns
        ignore_patterns = [
            '__pycache__',
            '.venv',
            'venv',
            '.git',
            'build',
            'dist',
            '*.egg-info'
        ]

        filtered_files = []
        for file_path in python_files:
            if not any(ignore in str(file_path) for ignore in ignore_patterns):
                filtered_files.append(file_path)

        return filtered_files

    def estimate_complexity(self, file_path: Path) -> int:
        """Estimate cyclomatic complexity for Python file."""
        try:
            content = file_path.read_text()
            lines = content.split('\n')

            complexity = 1  # Base complexity

            # Python-specific complexity keywords
            complexity_keywords = [
                'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except ',
                'with ', 'and ', 'or ', 'lambda', '?'  # ternary operator
            ]

            for line in lines:
                stripped = line.strip()
                for keyword in complexity_keywords:
                    if keyword in stripped:
                        complexity += 1

            return complexity

        except Exception:
            return 0

    def get_function_count(self, file_path: Path) -> int:
        """Count Python functions and methods."""
        try:
            content = file_path.read_text()
            lines = content.split('\n')

            function_count = 0
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('def ') or stripped.startswith('async def '):
                    function_count += 1

            return function_count

        except Exception:
            return 0

    def validate_function_length(self, file_path: Path, max_lines: int = 30) -> List[str]:
        """Check Python function lengths."""
        violations = []

        try:
            content = file_path.read_text()
            lines = content.split('\n')

            current_function = None
            function_start = 0
            indent_level = 0

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Detect function start
                if stripped.startswith('def ') or stripped.startswith('async def '):
                    # Check previous function
                    if current_function and (i - function_start) > max_lines:
                        violations.append(
                            f"{file_path.name}:{function_start + 1} - {current_function} "
                            f"exceeds {max_lines} lines ({i - function_start} lines)"
                        )

                    current_function = stripped.split('(')[0]
                    function_start = i
                    indent_level = len(line) - len(line.lstrip())

                # Detect function end (return to original indent level or less)
                elif current_function and line.strip() and len(line) - len(line.lstrip()) <= indent_level:
                    if not stripped.startswith(('def ', 'async def ', 'class ', '@')):
                        if (i - function_start) > max_lines:
                            violations.append(
                                f"{file_path.name}:{function_start + 1} - {current_function} "
                                f"exceeds {max_lines} lines ({i - function_start} lines)"
                            )
                        current_function = None

            # Check last function
            if current_function and (len(lines) - function_start) > max_lines:
                violations.append(
                    f"{file_path.name}:{function_start + 1} - {current_function} "
                    f"exceeds {max_lines} lines ({len(lines) - function_start} lines)"
                )

        except Exception as e:
            violations.append(f"Error analyzing {file_path}: {e}")

        return violations

    def format_code(self, file_path: Path) -> bool:
        """Format Python code using ruff."""
        try:
            result = self.run_command(f"ruff format {file_path}", cwd=file_path.parent)
            return result.returncode == 0
        except Exception:
            return False

    def get_dependencies(self, project_path: Path) -> List[str]:
        """Get Python dependencies from various sources."""
        dependencies = []

        # Check requirements.txt
        req_file = project_path / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text()
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name (before version specifiers)
                        package = re.split(r'[><=!]', line)[0].strip()
                        dependencies.append(package)
            except Exception:
                pass

        # Check pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists():
            try:
                import tomllib
                content = pyproject_file.read_text()
                data = tomllib.loads(content)

                # Check dependencies in project section
                project_deps = data.get('project', {}).get('dependencies', [])
                for dep in project_deps:
                    package = re.split(r'[><=!]', dep)[0].strip()
                    dependencies.append(package)

                # Check build system requirements
                build_deps = data.get('build-system', {}).get('requires', [])
                for dep in build_deps:
                    package = re.split(r'[><=!]', dep)[0].strip()
                    dependencies.append(package)

            except Exception:
                pass

        # Check setup.py (basic parsing)
        setup_file = project_path / "setup.py"
        if setup_file.exists():
            try:
                content = setup_file.read_text()
                # Look for install_requires
                install_requires_match = re.search(
                    r'install_requires\s*=\s*\[(.*?)\]',
                    content,
                    re.DOTALL
                )
                if install_requires_match:
                    deps_str = install_requires_match.group(1)
                    # Extract quoted strings
                    dep_matches = re.findall(r'["\']([^"\']+)["\']', deps_str)
                    for dep in dep_matches:
                        package = re.split(r'[><=!]', dep)[0].strip()
                        dependencies.append(package)
            except Exception:
                pass

        return list(set(dependencies))  # Remove duplicates

    def check_security_patterns(self, content: str) -> List[Dict[str, str]]:
        """Check for Python-specific security anti-patterns."""
        issues = super().check_security_patterns(content)

        # Python-specific patterns
        python_patterns = {
            "pickle_usage": r'import\s+pickle|pickle\.loads|pickle\.load',
            "eval_usage": r'\beval\s*\(',
            "exec_usage": r'\bexec\s*\(',
            "input_usage": r'\binput\s*\(',  # Python 2 input() is dangerous
            "yaml_unsafe": r'yaml\.load\s*\(',  # Should use safe_load
            "sql_string_format": r'(SELECT|INSERT|UPDATE|DELETE).*[%\{\}].*',
            "shell_true": r'shell\s*=\s*True',
            "temp_file_insecure": r'tempfile\.mktemp',
            "random_weak": r'random\.random|random\.choice',  # Should use secrets for crypto
        }

        for issue_type, pattern in python_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                severity = "high" if issue_type in ["eval_usage", "exec_usage", "pickle_usage"] else "medium"
                issues.append({
                    "type": issue_type,
                    "pattern": match.group(),
                    "severity": severity,
                    "line": content[:match.start()].count('\n') + 1
                })

        return issues

    def run_type_check(self, project_path: Path) -> Dict[str, Any]:
        """Run mypy type checking."""
        try:
            result = self.run_command("mypy .", cwd=project_path)

            # Parse mypy output
            errors = 0
            warnings = 0
            files_checked = 0

            for line in result.stdout.split('\n'):
                if ': error:' in line:
                    errors += 1
                elif ': warning:' in line:
                    warnings += 1
                elif 'Found' in line and 'error' in line:
                    # Summary line: "Found 5 errors in 3 files"
                    error_match = re.search(r'Found (\d+) error', line)
                    if error_match:
                        errors = int(error_match.group(1))

            return {
                "errors": errors,
                "warnings": warnings,
                "files_checked": files_checked,
                "success": errors == 0,
                "output": result.stdout
            }

        except Exception as e:
            return {"errors": -1, "success": False, "error": str(e)}

    def get_test_files(self, project_path: Path) -> List[Path]:
        """Get Python test files."""
        test_files = []

        # Common test patterns
        test_patterns = [
            "test_*.py",
            "*_test.py",
            "tests/**/*.py",
            "test/**/*.py"
        ]

        for pattern in test_patterns:
            test_files.extend(project_path.glob(pattern))

        # Filter out __init__.py and other non-test files
        actual_test_files = []
        for file_path in test_files:
            if file_path.name != "__init__.py":
                content = file_path.read_text()
                # Check if it actually contains tests
                if any(keyword in content for keyword in ['def test_', 'class Test', 'import pytest', 'import unittest']):
                    actual_test_files.append(file_path)

        return actual_test_files