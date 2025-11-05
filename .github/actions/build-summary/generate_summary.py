import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Set

# Platform mapping: artifact name -> display name
PLATFORM_MAPPING = {
    "wheels-linux-x86_64": "Linux x86_64",
    "wheels-linux-x86": "Linux x86",
    "wheels-linux-aarch64": "Linux aarch64",
    "wheels-linux-armv7": "Linux armv7",
    "wheels-linux-s390x": "Linux s390x",
    "wheels-linux-ppc64le": "Linux ppc64le",
    "wheels-musllinux-x86_64": "musllinux x86_64",
    "wheels-musllinux-x86": "musllinux x86",
    "wheels-musllinux-aarch64": "musllinux aarch64",
    "wheels-musllinux-armv7": "musllinux armv7",
    "wheels-windows-x64": "Windows x64",
    "wheels-windows-x86": "Windows x86",
    "wheels-windows-x64-freethreaded": "Windows x64",
    "wheels-windows-x86-freethreaded": "Windows x86",
    "wheels-windows-arm64": "Windows ARM64",
    "wheels-windows-arm64-freethreaded": "Windows ARM64",
    "wheels-macos-x86_64": "macOS x86_64",
    "wheels-macos-aarch64": "macOS aarch64",
}

# Define platform order for consistent display
PLATFORM_ORDER = [
    "Linux x86_64",
    "Linux x86",
    "Linux aarch64",
    "Linux armv7",
    "Linux s390x",
    "Linux ppc64le",
    "musllinux x86_64",
    "musllinux x86",
    "musllinux aarch64",
    "musllinux armv7",
    "Windows x64",
    "Windows x86",
    "Windows ARM64",
    "macOS x86_64",
    "macOS aarch64",
]

# Python versions to track (in order)
PYTHON_VERSIONS = [
    "3.8",
    "3.9",
    "3.10",
    "3.11",
    "3.12",
    "3.13",
    "3.14",
    "3.14t",
    "PyPy3.9",
    "PyPy3.10",
    "PyPy3.11",
]

# Wheel filename patterns to Python version mapping
VERSION_PATTERNS = {
    "cp38": "3.8",
    "cp39": "3.9",
    "cp310": "3.10",
    "cp311": "3.11",
    "cp312": "3.12",
    "cp313": "3.13",
    "cp314t": "3.14t",
    "cp314": "3.14",
    "pp39": "PyPy3.9",
    "pp310": "PyPy3.10",
    "pp311": "PyPy3.11",
}


def detect_python_version(filename: str) -> str | None:
    """Detect Python version from wheel filename."""
    # Check for freethreaded first (cp314t) before regular cp314
    if "cp314t" in filename:
        return "3.14t"

    for pattern, version in VERSION_PATTERNS.items():
        if pattern in filename:
            return version

    return None


def scan_wheels(wheels_path: Path) -> tuple[dict[str, Set[str]], Set[str]]:
    """
    Scan all wheel files and build a matrix of platform -> versions.

    Returns:
        - matrix: Dict mapping "platform|version" to presence indicator
        - seen_platforms: Set of platforms that have builds
    """
    matrix = defaultdict[str, Set[str]](set)
    seen_platforms = set[str]()

    # Find all .whl files
    for wheel_file in wheels_path.rglob("*.whl"):
        filename = wheel_file.name
        platform_dir = wheel_file.parent.name

        # Map platform directory name to display name
        platform = PLATFORM_MAPPING.get(platform_dir)
        if not platform:
            continue

        seen_platforms.add(platform)

        # Detect Python version from filename
        version = detect_python_version(filename)
        if version:
            matrix[platform].add(version)

    return matrix, seen_platforms


def generate_table(matrix: dict[str, Set[str]], seen_platforms: Set[str]) -> str:
    """Generate the markdown table."""
    lines: list[str] = []

    # Header
    lines.append("# Build Summary - All Platforms and Architectures")
    lines.append("")

    # Table header
    header = "| Platform | " + " | ".join(PYTHON_VERSIONS) + " |"
    separator = "|----------|" + "|".join(["-----"] * len(PYTHON_VERSIONS)) + "|"

    lines.append(header)
    lines.append(separator)

    # Table rows (only for platforms that were built)
    for platform in PLATFORM_ORDER:
        row = f"| **{platform}** |"

        for version in PYTHON_VERSIONS:
            if version in matrix[platform]:
                row += " ✅ |"
            else:
                row += " - |"

        lines.append(row)

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: generate_summary.py <wheels-path>", file=sys.stderr)
        sys.exit(1)

    wheels_path = Path(sys.argv[1])

    if not wheels_path.exists():
        print(f"Error: Path '{wheels_path}' does not exist", file=sys.stderr)
        sys.exit(1)

    matrix, seen_platforms = scan_wheels(wheels_path)

    table = generate_table(matrix, seen_platforms)

    if github_step_summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(github_step_summary, "a") as f:
            f.write(table + "\n")
    else:
        print(table)


if __name__ == "__main__":
    main()
