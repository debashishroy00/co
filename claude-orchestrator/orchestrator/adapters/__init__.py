"""
Language-specific adapters for the Claude Code Orchestrator.
Each adapter handles the specifics of different programming languages and ecosystems.
"""
from .base import BaseAdapter
from .python_adapter import PythonAdapter
from .typescript_adapter import TypeScriptAdapter
from .go_adapter import GoAdapter
from .rust_adapter import RustAdapter

ADAPTERS = {
    "python": PythonAdapter,
    "typescript": TypeScriptAdapter,
    "javascript": TypeScriptAdapter,  # Use TS adapter for JS
    "go": GoAdapter,
    "rust": RustAdapter,
}

def get_language_adapter(language: str) -> BaseAdapter:
    """Get the appropriate adapter for a programming language."""

    language = language.lower()
    adapter_class = ADAPTERS.get(language)

    if not adapter_class:
        # Fallback to closest match
        if "python" in language:
            adapter_class = PythonAdapter
        elif any(js in language for js in ["typescript", "javascript", "node", "react"]):
            adapter_class = TypeScriptAdapter
        elif "go" in language:
            adapter_class = GoAdapter
        elif "rust" in language:
            adapter_class = RustAdapter
        else:
            # Default fallback
            adapter_class = PythonAdapter

    return adapter_class()

__all__ = [
    "BaseAdapter",
    "PythonAdapter",
    "TypeScriptAdapter",
    "GoAdapter",
    "RustAdapter",
    "get_language_adapter",
    "ADAPTERS"
]