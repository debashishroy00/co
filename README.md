# Claude Code Orchestrator

A portable AI-assisted development pipeline that coordinates Builder, Reviewer, and Security agents to ensure every code change meets production standards.

## Quick Start

### Installation

```bash
pip install claude-orchestrator
```

### Initialize in Any Project

```bash
cd your-project
orchestrator-init
```

The init command auto-detects your project type (Python, TypeScript, Go, Rust, React) and creates appropriate configuration.

### Use with Claude Code

1. **Activate orchestrator mode** in Claude Code:
   ```
   "Use orchestrator mode for all coding tasks. Check .claude/orchestrator.json for config."
   ```

2. **Give coding tasks as normal**:
   ```
   "Add input validation to the API endpoints"
   "Optimize the search algorithm for better performance"
   "Add error handling to the file upload feature"
   ```

3. **Get executive summaries** instead of verbose logs:
   ```
   🤖 ORCHESTRATOR REPORT
   Task: Add input validation to API endpoints
   Decision: PROMOTE ✅

   CHANGES:
   - Added validation to UserRequest model
   - Implemented security checks for XSS/injection
   - Added comprehensive test suite

   RESULTS:
   - Tests: ✅ 23/23 passed
   - Security: ✅ CLEAR
   - Performance: ✅ <1ms overhead
   - Coverage: ✅ 94%

   NEXT: Ready to merge
   ```

## How It Works

### The Pipeline
```
TASK → BUILD → CI → REVIEW → SECURITY → DECIDE → DOCS → REPORT
         ↑                                    ↓
         └─────── RETRY (max 2) ─────────────┘
```

### Agent Coordination
- **Builder Agent**: Generates code following project standards
- **CI Pipeline**: Runs tests, benchmarks, security scans automatically
- **Reviewer Agent**: Checks code quality, patterns, simplicity
- **Security Agent**: Scans for vulnerabilities, secrets, injection risks
- **Orchestrator**: Makes PROMOTE/HOLD decisions based on all results

### Quality Gates
Every change must pass:
- ✅ **Build**: Code compiles without errors
- ✅ **Tests**: All tests pass, coverage ≥80%
- ✅ **Review**: Functions ≤30 lines, follows patterns
- ✅ **Security**: No high-severity issues
- ✅ **Performance**: Metrics within bounds

## Supported Project Types

The orchestrator auto-detects and configures for:

| Type | Languages | Frameworks | Tools |
|------|-----------|------------|-------|
| **Python ML** | Python | scikit-learn, tensorflow, pytorch | pytest, ruff, bandit, mypy |
| **Python API** | Python | FastAPI, Django, Flask | pytest, ruff, bandit, uvicorn |
| **TypeScript Node** | TypeScript | Express, NestJS, CLI tools | vitest, eslint, semgrep |
| **React Frontend** | TypeScript/JS | React, Next.js, Vite | vitest, eslint, lighthouse |
| **Go Service** | Go | Gin, Echo, gRPC | go test, golangci-lint, gosec |
| **Rust Project** | Rust | Tokio, Actix, Clap | cargo test, clippy, audit |

## Configuration

After running `orchestrator-init`, customize `.claude/orchestrator.json`:

```json
{
  "project_name": "my-awesome-project",
  "language": "python",
  "project_type": "api",
  "tools": {
    "test": "pytest --cov=src tests/",
    "lint": "ruff check .",
    "security": "bandit -r src/",
    "format": "ruff format ."
  },
  "metrics": {
    "performance": {
      "response_time": {"target": -5, "cap": 10, "unit": "%"},
      "memory_usage": {"target": 0, "cap": 15, "unit": "%"}
    },
    "quality": {
      "test_coverage": {"target": 80, "absolute": true, "unit": "%"}
    }
  },
  "standards": {
    "max_function_lines": 30,
    "test_coverage": 80,
    "security_level": "no-high"
  }
}
```

## Command Line Usage

### Run Orchestrator Directly
```bash
# Run on a specific task
orchestrator run "Add caching to user profiles"

# Target specific files
orchestrator run "Optimize database queries" -f src/models.py -f src/db.py

# Dry run to see plan
orchestrator run "Add error handling" --dry-run
```

### Project Management
```bash
# Check orchestrator status
orchestrator status

# Test CI pipeline
orchestrator test ci

# Export configuration
orchestrator export-config --format yaml
```

### Record Metrics
```bash
# Record benchmark results
orchestrator benchmark response_time -2.5  # 2.5% improvement
orchestrator benchmark memory_usage +1.2   # 1.2% increase
```

## Integration Examples

### GitHub Actions
```yaml
name: Orchestrator CI
on: [push, pull_request]
jobs:
  orchestrator:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install claude-orchestrator
      - run: orchestrator test ci
      - run: orchestrator test tools
```

### VS Code Tasks
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Orchestrator Status",
      "type": "shell",
      "command": "orchestrator status"
    },
    {
      "label": "Test CI Pipeline",
      "type": "shell",
      "command": "orchestrator test ci"
    }
  ]
}
```

### Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit
orchestrator test ci || exit 1
```

## Custom Metrics

Define domain-specific metrics for your project:

```json
{
  "metrics": {
    "ml_performance": {
      "model_accuracy": {"target": 0.95, "absolute": true},
      "training_time": {"target": -10, "cap": 20, "unit": "%"},
      "inference_latency": {"target": -5, "cap": 15, "unit": "%"}
    },
    "api_performance": {
      "response_time_p95": {"target": -5, "cap": 10, "unit": "%"},
      "throughput": {"target": 5, "cap": -10, "unit": "%"},
      "error_rate": {"target": 0, "cap": 0.1, "unit": "%"}
    },
    "frontend_performance": {
      "bundle_size": {"target": 0, "cap": 5, "unit": "%"},
      "lighthouse_score": {"target": 95, "absolute": true},
      "first_contentful_paint": {"target": -10, "cap": 10, "unit": "%"}
    }
  }
}
```

## Benefits

### For Developers
- **Faster iteration**: Automated reviews catch issues early
- **Learn best practices**: AI agents enforce consistent patterns
- **Focus on creativity**: Spend time on algorithms, not formatting

### For Teams
- **Consistent quality**: Every PR meets the same standards
- **Reduced review burden**: Human reviewers focus on architecture
- **Knowledge sharing**: Standards are codified and enforced

### For Stakeholders
- **Production confidence**: Every change is tested and secured
- **Velocity tracking**: Metrics show continuous improvement
- **Audit trail**: Complete change history with quality evidence

## Advanced Features

### Multi-Language Projects
```json
{
  "language": "multi",
  "tools": {
    "backend": {
      "test": "pytest tests/",
      "lint": "ruff check backend/"
    },
    "frontend": {
      "test": "npm test",
      "lint": "npm run lint"
    }
  }
}
```

### Custom Agents
```python
# Add to .claude/custom_agents.py
class DomainExpertAgent:
    def review_ml_model(self, patch, metrics):
        # Custom review logic for ML models
        pass
```

### Conditional Rules
```json
{
  "rules": {
    "if_files_match": "*.py",
    "then_require": ["type_hints", "docstrings"],
    "if_performance_critical": true,
    "then_benchmark": ["latency", "memory"]
  }
}
```

## Migration from Existing Projects

1. **Install orchestrator**: `pip install claude-orchestrator`
2. **Initialize**: `orchestrator-init` (detects existing setup)
3. **Customize**: Edit `.claude/orchestrator.json` for your needs
4. **Test**: `orchestrator test ci` to verify tools work
5. **Integrate**: Add to CI/CD and development workflow

## Contributing

The orchestrator is designed to be extensible:

- **Language Adapters**: Add support for new languages
- **Metric Collectors**: Add domain-specific measurements
- **Quality Gates**: Define custom validation rules
- **Agent Prompts**: Improve AI agent effectiveness

## License

MIT License - see LICENSE file for details.

---

**Transform any codebase into a production-ready, investor-grade development pipeline with AI-assisted quality assurance.**
