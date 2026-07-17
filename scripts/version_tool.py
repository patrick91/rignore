"""Release version helper used by CI.

Two modes, deliberately split so build runners never need autopub:

* ``compute`` — ask autopub what the next version is (reads RELEASE.md +
  the current version). Needs autopub, so it only runs on Linux where a
  cryptography wheel is available.
* ``apply <version>`` — write that version into pyproject.toml, Cargo.toml,
  and Cargo.lock. Needs only tomlkit (pure Python), so it runs on every
  wheel-build platform, including windows-arm.
"""

from __future__ import annotations

import argparse
import pathlib


def _crate_name(cargo: object) -> str:
    return str(cargo["package"]["name"])  # type: ignore[index]


def _apply(version: str) -> None:
    import tomlkit

    pyproject_path = pathlib.Path("pyproject.toml")
    pyproject = tomlkit.parse(pyproject_path.read_text())
    pyproject["project"]["version"] = version  # type: ignore[index]
    pyproject_path.write_text(tomlkit.dumps(pyproject))

    cargo_path = pathlib.Path("Cargo.toml")
    cargo = tomlkit.parse(cargo_path.read_text())
    cargo["package"]["version"] = version  # type: ignore[index]
    cargo_path.write_text(tomlkit.dumps(cargo))

    # Keep Cargo.lock in sync so maturin's `--locked` build stays happy.
    crate = _crate_name(cargo)
    lock_path = pathlib.Path("Cargo.lock")
    lock = tomlkit.parse(lock_path.read_text())
    for package in lock.get("package", []):
        if package.get("name") == crate:
            package["version"] = version
            break
    lock_path.write_text(tomlkit.dumps(lock))


def _compute() -> str:
    import sys

    sys.path.insert(0, ".")

    from autopub import Autopub
    from autopub.plugins.bump_version import BumpVersionPlugin

    from scripts.autopub_rignore import RignorePlugin

    autopub = Autopub(plugins=[BumpVersionPlugin, RignorePlugin])
    autopub.check()

    version = autopub.release_info.version
    if version is None:
        raise SystemExit("autopub did not compute a release version")
    return version


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("compute")
    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("version")

    args = parser.parse_args()

    if args.command == "compute":
        print(_compute())
    elif args.command == "apply":
        _apply(args.version)


if __name__ == "__main__":
    main()
