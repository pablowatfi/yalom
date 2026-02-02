#!/usr/bin/env python3
"""
View and manage prompt versions.

Usage:
    poetry run python view_prompts.py              # List all versions
    poetry run python view_prompts.py --show 1.1.0  # Show specific version
    poetry run python view_prompts.py --active      # Show active version
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.rag.prompts import list_versions, get_prompt, ACTIVE_VERSION


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--active":
            # Show active version
            print("=" * 80)
            print(f"ACTIVE PROMPT VERSION: {ACTIVE_VERSION}")
            print("=" * 80)
            print()
            prompt = get_prompt()
            print(f"Version: {prompt['version']}")
            print(f"Date: {prompt['date']}")
            print()
            print("System Prompt:")
            print("-" * 80)
            print(prompt['system'])
            print()
            print("Human Template:")
            print("-" * 80)
            print(prompt['human'])
            print()

        elif arg == "--show":
            # Show specific version
            if len(sys.argv) < 3:
                print("Error: --show requires a version number")
                print("Example: poetry run python view_prompts.py --show 1.0.0")
                return 1

            version = sys.argv[2]
            prompt = get_prompt(version)
            print("=" * 80)
            print(f"PROMPT VERSION: {version}")
            print("=" * 80)
            print()
            print(f"Date: {prompt['date']}")
            print()
            print("System Prompt:")
            print("-" * 80)
            print(prompt['system'])
            print()
            print("Human Template:")
            print("-" * 80)
            print(prompt['human'])
            print()
        else:
            print("Unknown argument. Use --active or --show <version>")
            return 1
    else:
        # List all versions
        print("=" * 80)
        print("AVAILABLE PROMPT VERSIONS")
        print("=" * 80)
        print()

        versions = list_versions()
        for v in versions:
            status = " [ACTIVE]" if v["is_active"] else ""
            print(f"Version {v['version']}{status}")
            print(f"  Date: {v['date']}")
            print(f"  Changes: {v['changelog']}")
            print()

        print("=" * 80)
        print()
        print("To view a specific version:")
        print("  poetry run python view_prompts.py --show 1.1.0")
        print()
        print("To view the active version:")
        print("  poetry run python view_prompts.py --active")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
