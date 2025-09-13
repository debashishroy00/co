"""
Claude Code Orchestrator Package
Portable AI-assisted development pipeline for any project.
"""
from setuptools import setup, find_packages

setup(
    name="claude-orchestrator",
    version="1.0.0",
    description="AI-assisted development pipeline with Builder/Reviewer/Security agents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="CEGO Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
        "click>=8.0.0",
        "psutil>=5.8.0",
        "tiktoken>=0.4.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
        "security": [
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "orchestrator=orchestrator.cli:main",
            "orchestrator-init=orchestrator.init:init_project",
        ]
    },
    include_package_data=True,
    package_data={
        "orchestrator": [
            "templates/*.json",
            "templates/*.yaml",
            "templates/*.md",
            "adapters/*.py"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
)