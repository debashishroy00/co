"""
Command-line interface for Claude Code Orchestrator.
Main entry point for running orchestration tasks.
"""
import click
import json
import sys
from pathlib import Path
from typing import List, Optional

from .core import Orchestrator, TaskSpec
from .adapters import get_language_adapter


@click.group()
@click.version_option()
def main():
    """Claude Code Orchestrator - AI-assisted development pipeline."""
    pass


@main.command()
@click.argument('task_description')
@click.option('--files', '-f', multiple=True, help='Target files to modify')
@click.option('--config', '-c', default='.claude/orchestrator.json', help='Config file path')
@click.option('--dry-run', is_flag=True, help='Show plan without executing')
@click.option('--max-tokens', type=int, help='Maximum tokens for task')
def run(task_description: str, files: tuple, config: str, dry_run: bool, max_tokens: Optional[int]):
    """Run orchestrator on a task."""

    # Load configuration
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"❌ Config file not found: {config_path}")
        click.echo("Run 'orchestrator-init' to initialize the project.")
        sys.exit(1)

    try:
        with open(config_path) as f:
            orchestrator_config = json.load(f)
    except Exception as e:
        click.echo(f"❌ Error loading config: {e}")
        sys.exit(1)

    # Create task specification
    spec = TaskSpec(
        task=task_description,
        targets=list(files) if files else [],
        acceptance=orchestrator_config.get('gates', {}),
        context=""
    )

    if dry_run:
        click.echo("🔍 DRY RUN - Task specification:")
        click.echo(f"Task: {spec.task}")
        click.echo(f"Targets: {spec.targets}")
        click.echo(f"Config: {orchestrator_config['project_name']} ({orchestrator_config['language']})")
        return

    # Initialize orchestrator
    orchestrator = Orchestrator(config_path=str(config_path))

    click.echo(f"🤖 Starting orchestrator for: {task_description}")
    click.echo(f"📋 Project: {orchestrator_config['project_name']}")
    click.echo(f"🔧 Language: {orchestrator_config['language']}")

    # Run orchestration
    try:
        report = orchestrator.run_full_pipeline(spec)
        click.echo("\n" + "="*60)
        click.echo(report)
    except Exception as e:
        click.echo(f"❌ Orchestration failed: {e}")
        sys.exit(1)


@main.command()
@click.option('--config', '-c', default='.claude/orchestrator.json', help='Config file path')
def status(config: str):
    """Show orchestrator status and configuration."""

    config_path = Path(config)
    if not config_path.exists():
        click.echo("❌ Orchestrator not initialized in this project.")
        click.echo("Run 'orchestrator-init' to get started.")
        return

    with open(config_path) as f:
        orchestrator_config = json.load(f)

    click.echo("🤖 Claude Code Orchestrator Status")
    click.echo("="*40)
    click.echo(f"Project: {orchestrator_config['project_name']}")
    click.echo(f"Type: {orchestrator_config['project_type']}")
    click.echo(f"Language: {orchestrator_config['language']}")
    click.echo(f"Version: {orchestrator_config.get('orchestrator_version', 'unknown')}")

    click.echo(f"\n🔧 Tools:")
    for tool, command in orchestrator_config['tools'].items():
        click.echo(f"  {tool}: {command}")

    click.echo(f"\n📊 Metrics:")
    for category, metrics in orchestrator_config['metrics'].items():
        click.echo(f"  {category}:")
        for metric, config in metrics.items():
            if isinstance(config, dict):
                target = config.get('target', 'N/A')
                unit = config.get('unit', '')
                click.echo(f"    {metric}: target {target}{unit}")

    click.echo(f"\n🚪 Quality Gates:")
    for gate, description in orchestrator_config['gates'].items():
        click.echo(f"  {gate}: {description}")


@main.command()
@click.argument('test_type', type=click.Choice(['ci', 'tools', 'config']))
@click.option('--config', '-c', default='.claude/orchestrator.json', help='Config file path')
def test(test_type: str, config: str):
    """Test orchestrator components."""

    config_path = Path(config)
    if not config_path.exists():
        click.echo("❌ Orchestrator not initialized.")
        return

    with open(config_path) as f:
        orchestrator_config = json.load(f)

    orchestrator = Orchestrator(config_path=str(config_path))

    if test_type == 'ci':
        click.echo("🧪 Testing CI pipeline...")
        result = orchestrator.run_ci_pipeline()
        if result.success:
            click.echo("✅ CI pipeline test passed")
        else:
            click.echo(f"❌ CI pipeline test failed: {result.output}")

    elif test_type == 'tools':
        click.echo("🔧 Testing tool availability...")
        adapter = get_language_adapter(orchestrator_config['language'])

        for tool_name, command in orchestrator_config['tools'].items():
            try:
                success = adapter.test_tool(command)
                status = "✅" if success else "❌"
                click.echo(f"  {status} {tool_name}: {command}")
            except Exception as e:
                click.echo(f"  ❌ {tool_name}: {e}")

    elif test_type == 'config':
        click.echo("⚙️  Testing configuration...")

        required_fields = ['project_name', 'language', 'tools', 'metrics', 'gates']
        for field in required_fields:
            if field in orchestrator_config:
                click.echo(f"  ✅ {field}: present")
            else:
                click.echo(f"  ❌ {field}: missing")

        # Test tool commands are strings
        for tool, command in orchestrator_config['tools'].items():
            if isinstance(command, str):
                click.echo(f"  ✅ {tool} command: valid")
            else:
                click.echo(f"  ❌ {tool} command: invalid type")


@main.command()
@click.option('--config', '-c', default='.claude/orchestrator.json', help='Config file path')
@click.option('--format', 'output_format', type=click.Choice(['json', 'yaml']), default='json', help='Output format')
def export_config(config: str, output_format: str):
    """Export orchestrator configuration."""

    config_path = Path(config)
    if not config_path.exists():
        click.echo("❌ Config file not found.")
        return

    with open(config_path) as f:
        orchestrator_config = json.load(f)

    if output_format == 'json':
        click.echo(json.dumps(orchestrator_config, indent=2))
    elif output_format == 'yaml':
        import yaml
        click.echo(yaml.dump(orchestrator_config, default_flow_style=False))


@main.command()
@click.argument('metric_name')
@click.argument('value', type=float)
@click.option('--config', '-c', default='.claude/orchestrator.json', help='Config file path')
def benchmark(metric_name: str, value: float, config: str):
    """Record a benchmark result."""

    # Create ci directory if it doesn't exist
    ci_dir = Path("ci")
    ci_dir.mkdir(exist_ok=True)

    # Read existing benchmark data
    benchmark_file = ci_dir / "BENCH_SUMMARY.txt"

    if benchmark_file.exists():
        content = benchmark_file.read_text().strip()
        # Parse existing metrics
        if content.startswith("BENCH:"):
            content = content[6:].strip()  # Remove "BENCH:" prefix
        metrics = {}
        for part in content.split():
            if ':' in part:
                key, val = part.split(':', 1)
                metrics[key] = val
    else:
        metrics = {}

    # Update with new value
    metrics[metric_name] = f"{value:+.1f}%"

    # Write back
    benchmark_line = "BENCH: " + " ".join(f"{k}:{v}" for k, v in metrics.items())
    with open(benchmark_file, 'w') as f:
        f.write(benchmark_line + '\n')

    click.echo(f"📊 Recorded {metric_name}: {value:+.1f}%")
    click.echo(f"💾 Updated: {benchmark_file}")


if __name__ == "__main__":
    main()