import os
from pathlib import Path
import shutil
from typing import List


def create_directory_structure():
    """Create the project directory structure."""
    # Base directories
    directories = [
        "src/core/config",
        "src/core/tracking",
        "src/core/utils",
        "src/models",
        "src/storage",
        "src/components/bar_finder",
        "src/components/menu_scraper",
        "src/components/menu_analyzer",
        "src/pipeline",
        "tests/test_bar_finder",
        "tests/test_menu_scraper",
        "tests/test_menu_analyzer",
        "scripts",
    ]

    # Create directories
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Create __init__.py in each Python package directory
        if directory.startswith(('src/', 'tests/')):
            init_file = Path(directory) / "__init__.py"
            init_file.touch(exist_ok=True)


def create_file_templates():
    """Create template files with basic content."""
    files = {
        # Core
        "src/core/config/model_configs.py": '''"""Model configurations and constants."""
MODEL_CONFIGS = {
    'gpt-3.5-turbo': {
        'name': 'gpt-3.5-turbo',
        'max_tokens': 4096,
        'cost_per_1k_input': 0.0005,
        'cost_per_1k_output': 0.0015
    }
}''',
        "src/core/config/settings.py": '''"""Global settings and configuration."""
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
''',

        # Components
        "src/components/bar_finder/search.py": '''"""Bar search implementation."""
from typing import List, Dict

class BarSearch:
    """Handle bar search operations."""
    def __init__(self):
        pass
''',

        # Pipeline
        "src/pipeline/orchestrator.py": '''"""Pipeline orchestration."""
class PipelineOrchestrator:
    """Coordinate pipeline components."""
    def __init__(self):
        pass
''',

        # Tasks
        "tasks.py": '''"""Invoke tasks for the project."""
from invoke import task

@task
def setup(ctx):
    """Set up the project."""
    ctx.run("uv pip install -e .")

@task
def test(ctx):
    """Run tests."""
    ctx.run("pytest tests/")

@task
def lint(ctx):
    """Run linting."""
    ctx.run("ruff check .")
''',

        # Project configuration
        "pyproject.toml": '''[project]
name = "cocktail-scraper"
version = "0.1.0"
description = "Cocktail menu analysis pipeline"
dependencies = [
    "crewai",
    "langchain-community",
    "tiktoken",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
''',
    }

    for file_path, content in files.items():
        file = Path(file_path)
        file.parent.mkdir(parents=True, exist_ok=True)
        if not file.exists():  # Don't overwrite existing files
            file.write_text(content)


def move_existing_files():
    """Move existing files to their new locations."""
    moves = [
        ("src/utils.py", "src/core/utils/utils.py"),
        ("src/cocktail_research/cocktail_scraper.py", "src/components/bar_finder/scraper.py"),
        ("src/cocktail_research/crew_cocktail_scraper.py", "src/components/bar_finder/crew_scraper.py"),
    ]

    for old_path, new_path in moves:
        if Path(old_path).exists():
            Path(new_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(old_path, new_path)


def main():
    """Main setup function."""
    print("Setting up project structure...")
    create_directory_structure()

    print("Creating file templates...")
    create_file_templates()

    print("Moving existing files...")
    move_existing_files()

    print("\nSetup complete! Next steps:")
    print("1. Run 'invoke setup' to install the package")
    print("2. Review and adjust the moved files")
    print("3. Update pyproject.toml with any additional dependencies")


if __name__ == "__main__":
    main()