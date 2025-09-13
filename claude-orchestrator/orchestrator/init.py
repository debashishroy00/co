"""
Project initialization script for Claude Code Orchestrator.
Automatically detects project type and sets up configuration.
"""
import os
import json
import click
from pathlib import Path
from typing import Dict, Any


PROJECT_TEMPLATES = {
    "python_ml": {
        "description": "Python ML/AI project with scikit-learn, tensorflow, etc.",
        "indicators": ["requirements.txt", "setup.py", "pyproject.toml"],
        "keywords": ["tensorflow", "torch", "sklearn", "numpy", "pandas", "jupyter"],
        "config": {
            "language": "python",
            "project_type": "ml",
            "tools": {
                "lint": "ruff check .",
                "format": "ruff format .",
                "test": "pytest --cov=src tests/",
                "security": "bandit -r src/ && safety check",
                "typecheck": "mypy src/"
            },
            "metrics": {
                "performance": {
                    "training_time": {"target": -10, "cap": 20, "unit": "%"},
                    "inference_latency": {"target": -5, "cap": 15, "unit": "%"},
                    "memory_usage": {"target": 0, "cap": 20, "unit": "%"}
                },
                "quality": {
                    "test_coverage": {"target": 80, "absolute": True, "unit": "%"},
                    "model_accuracy": {"target": 0.85, "absolute": True, "unit": "score"}
                }
            }
        }
    },
    "python_api": {
        "description": "Python API/web service (FastAPI, Django, Flask)",
        "indicators": ["requirements.txt", "app.py", "main.py", "manage.py"],
        "keywords": ["fastapi", "django", "flask", "uvicorn", "gunicorn"],
        "config": {
            "language": "python",
            "project_type": "api",
            "tools": {
                "lint": "ruff check .",
                "format": "ruff format .",
                "test": "pytest --cov=. tests/",
                "security": "bandit -r . && safety check",
                "typecheck": "mypy ."
            },
            "metrics": {
                "performance": {
                    "response_time": {"target": -5, "cap": 10, "unit": "%"},
                    "throughput": {"target": 5, "cap": -10, "unit": "%"},
                    "memory_usage": {"target": 0, "cap": 15, "unit": "%"}
                }
            }
        }
    },
    "typescript_node": {
        "description": "TypeScript/Node.js project (API, CLI, library)",
        "indicators": ["package.json", "tsconfig.json"],
        "keywords": ["typescript", "node", "express", "nestjs"],
        "config": {
            "language": "typescript",
            "project_type": "node",
            "tools": {
                "lint": "eslint . --max-warnings 0",
                "format": "prettier --write .",
                "test": "vitest --run --coverage",
                "security": "npm audit && semgrep --config auto",
                "typecheck": "tsc --noEmit",
                "build": "npm run build"
            },
            "metrics": {
                "performance": {
                    "response_time": {"target": -5, "cap": 10, "unit": "%"},
                    "memory_usage": {"target": 0, "cap": 15, "unit": "%"},
                    "bundle_size": {"target": 0, "cap": 5, "unit": "%"}
                }
            }
        }
    },
    "react_frontend": {
        "description": "React frontend application",
        "indicators": ["package.json", "src/App.tsx", "src/App.jsx", "public/index.html"],
        "keywords": ["react", "next", "vite", "webpack"],
        "config": {
            "language": "typescript",
            "project_type": "frontend",
            "tools": {
                "lint": "eslint . --max-warnings 0",
                "format": "prettier --write .",
                "test": "vitest --run --coverage",
                "security": "npm audit",
                "typecheck": "tsc --noEmit",
                "build": "npm run build"
            },
            "metrics": {
                "performance": {
                    "bundle_size": {"target": 0, "cap": 5, "unit": "%"},
                    "lighthouse_performance": {"target": 90, "absolute": True, "unit": "score"},
                    "first_contentful_paint": {"target": -10, "cap": 10, "unit": "%"}
                }
            }
        }
    },
    "go_service": {
        "description": "Go microservice or CLI application",
        "indicators": ["go.mod", "main.go"],
        "keywords": ["gin", "echo", "chi", "gorilla", "grpc"],
        "config": {
            "language": "go",
            "project_type": "service",
            "tools": {
                "lint": "golangci-lint run",
                "format": "gofmt -w . && goimports -w .",
                "test": "go test -v -race -cover ./...",
                "security": "gosec ./...",
                "build": "go build -o bin/ ./..."
            },
            "metrics": {
                "performance": {
                    "response_time": {"target": -5, "cap": 10, "unit": "%"},
                    "memory_usage": {"target": 0, "cap": 15, "unit": "%"},
                    "binary_size": {"target": 0, "cap": 10, "unit": "%"}
                }
            }
        }
    },
    "rust_project": {
        "description": "Rust application or library",
        "indicators": ["Cargo.toml", "src/main.rs", "src/lib.rs"],
        "keywords": ["tokio", "serde", "clap", "actix", "warp"],
        "config": {
            "language": "rust",
            "project_type": "application",
            "tools": {
                "lint": "cargo clippy -- -D warnings",
                "format": "cargo fmt",
                "test": "cargo test",
                "security": "cargo audit",
                "build": "cargo build --release"
            },
            "metrics": {
                "performance": {
                    "compile_time": {"target": -5, "cap": 20, "unit": "%"},
                    "binary_size": {"target": 0, "cap": 10, "unit": "%"},
                    "memory_usage": {"target": -10, "cap": 5, "unit": "%"}
                }
            }
        }
    }
}


def detect_project_type(project_path: Path) -> str:
    """Auto-detect project type based on files and content."""

    # Check for specific files
    files_in_project = set()
    for root, dirs, files in os.walk(project_path):
        # Skip deep nested directories and common ignore patterns
        if any(ignore in root for ignore in ['.git', 'node_modules', '__pycache__', '.venv']):
            continue
        if root.count(os.sep) - str(project_path).count(os.sep) > 3:
            continue

        files_in_project.update(files)

    # Check package files for keywords
    keywords_found = set()
    for file_name in ['package.json', 'requirements.txt', 'Cargo.toml', 'go.mod', 'pyproject.toml']:
        file_path = project_path / file_name
        if file_path.exists():
            try:
                content = file_path.read_text().lower()
                for template_name, template in PROJECT_TEMPLATES.items():
                    for keyword in template['keywords']:
                        if keyword in content:
                            keywords_found.add(template_name)
            except:
                pass

    # Score each template
    scores = {}
    for template_name, template in PROJECT_TEMPLATES.items():
        score = 0

        # Check file indicators
        for indicator in template['indicators']:
            if indicator in files_in_project:
                score += 3

        # Check keywords
        if template_name in keywords_found:
            score += 5

        scores[template_name] = score

    # Return best match or default
    if scores and max(scores.values()) > 0:
        return max(scores, key=scores.get)

    return "python_api"  # Default fallback


def create_orchestrator_config(project_path: Path, project_type: str, custom_name: str = None) -> Dict[str, Any]:
    """Create orchestrator configuration for the project."""

    template = PROJECT_TEMPLATES[project_type]
    config = template['config'].copy()

    # Add project-specific metadata
    config.update({
        "project_name": custom_name or project_path.name,
        "project_type": project_type,
        "orchestrator_version": "1.0.0",
        "standards": {
            "max_function_lines": 30,
            "test_coverage": 80,
            "security_level": "no-high",
            "documentation_required": True
        },
        "gates": {
            "build": "All code compiles without errors",
            "test": "All tests pass, coverage >= 80%",
            "review": "Code follows standards, functions <= 30 lines",
            "security": "No high severity issues, no hardcoded secrets",
            "performance": "Metrics within acceptable bounds"
        }
    })

    return config


@click.command()
@click.option('--project-path', default='.', help='Path to project directory')
@click.option('--project-type', help='Force specific project type')
@click.option('--project-name', help='Custom project name')
@click.option('--dry-run', is_flag=True, help='Show what would be created without creating')
def init_project(project_path: str, project_type: str, project_name: str, dry_run: bool):
    """Initialize Claude Code Orchestrator in a project."""

    path = Path(project_path).resolve()

    if not path.exists():
        click.echo(f"❌ Path does not exist: {path}")
        return

    click.echo(f"🔍 Analyzing project at: {path}")

    # Detect or use provided project type
    if not project_type:
        detected_type = detect_project_type(path)
        click.echo(f"🎯 Detected project type: {detected_type}")

        # Show available types
        click.echo("\nAvailable project types:")
        for name, template in PROJECT_TEMPLATES.items():
            marker = "👈 (detected)" if name == detected_type else "  "
            click.echo(f"  {name}: {template['description']} {marker}")

        if not click.confirm(f"\nUse detected type '{detected_type}'?"):
            project_type = click.prompt(
                "Enter project type",
                type=click.Choice(list(PROJECT_TEMPLATES.keys()))
            )
        else:
            project_type = detected_type

    # Validate project type
    if project_type not in PROJECT_TEMPLATES:
        click.echo(f"❌ Unknown project type: {project_type}")
        return

    template = PROJECT_TEMPLATES[project_type]
    click.echo(f"✅ Using project type: {project_type}")
    click.echo(f"   Description: {template['description']}")

    # Create configuration
    config = create_orchestrator_config(path, project_type, project_name)

    # Show what will be created
    claude_dir = path / ".claude"
    orchestrator_config = claude_dir / "orchestrator.json"
    ci_dir = path / "ci"

    click.echo(f"\n📁 Files to be created:")
    click.echo(f"   {orchestrator_config}")
    click.echo(f"   {ci_dir / 'pipeline.py'}")
    click.echo(f"   {ci_dir / 'README.md'}")

    if dry_run:
        click.echo("\n🔍 DRY RUN - Configuration preview:")
        click.echo(json.dumps(config, indent=2))
        return

    # Create directories
    claude_dir.mkdir(exist_ok=True)
    ci_dir.mkdir(exist_ok=True)

    # Write orchestrator config
    with open(orchestrator_config, 'w') as f:
        json.dump(config, f, indent=2)

    # Copy CI pipeline
    pipeline_template = Path(__file__).parent / "templates" / "pipeline.py"
    ci_pipeline = ci_dir / "pipeline.py"

    if pipeline_template.exists():
        import shutil
        shutil.copy(pipeline_template, ci_pipeline)
    else:
        # Fallback: create basic pipeline
        basic_pipeline = f'''"""
CI Pipeline for {config['project_name']}
Auto-generated by Claude Code Orchestrator
"""

import subprocess
import json
from pathlib import Path

def run_tests():
    cmd = "{config['tools']['test']}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    return result.returncode == 0

def run_lint():
    cmd = "{config['tools']['lint']}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    return result.returncode == 0

def run_security():
    cmd = "{config['tools']['security']}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True)
    return result.returncode == 0

if __name__ == "__main__":
    print("🚀 Running CI pipeline...")

    results = {{
        "tests": run_tests(),
        "lint": run_lint(),
        "security": run_security()
    }}

    print(f"Results: {{results}}")
'''

        with open(ci_pipeline, 'w') as f:
            f.write(basic_pipeline)

    # Create CI README
    ci_readme = ci_dir / "README.md"
    with open(ci_readme, 'w') as f:
        f.write(f"""# CI Pipeline for {config['project_name']}

This directory contains the CI pipeline configuration for the Claude Code Orchestrator.

## Commands

- **Tests**: `{config['tools']['test']}`
- **Lint**: `{config['tools']['lint']}`
- **Security**: `{config['tools']['security']}`

## Metrics

The pipeline tracks these metrics:
{json.dumps(config['metrics'], indent=2)}

## Usage

Run the full pipeline:
```bash
python ci/pipeline.py
```

Or use with orchestrator:
```bash
orchestrator "Add new feature X"
```
""")

    click.echo(f"\n✅ Orchestrator initialized for {project_type} project!")
    click.echo(f"📋 Configuration: {orchestrator_config}")
    click.echo(f"🔧 CI Pipeline: {ci_pipeline}")

    click.echo(f"\n🚀 Next steps:")
    click.echo(f"1. Review the configuration in {orchestrator_config}")
    click.echo(f"2. Customize metrics and tools as needed")
    click.echo(f"3. Test the pipeline: python {ci_pipeline}")
    click.echo(f"4. Use Claude Code with orchestrator mode activated")


if __name__ == "__main__":
    init_project()