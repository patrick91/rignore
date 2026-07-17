from __future__ import annotations

import pathlib
import subprocess

import tomlkit

from autopub.exceptions import AutopubException
from autopub.plugins import AutopubPlugin
from autopub.types import ReleaseInfo


class RignorePlugin(AutopubPlugin):
    id = "rignore"

    def _read_toml(self, path: pathlib.Path) -> tomlkit.TOMLDocument:
        return tomlkit.parse(path.read_text())

    def _write_toml(self, path: pathlib.Path, data: tomlkit.TOMLDocument) -> None:
        path.write_text(tomlkit.dumps(data))

    def _project_version(self) -> str:
        pyproject = self._read_toml(pathlib.Path("pyproject.toml"))

        try:
            version = pyproject["project"]["version"]  # type: ignore[index]
        except KeyError as exc:
            raise AutopubException("pyproject.toml must define project.version") from exc

        return str(version)

    def _cargo_version(self) -> str:
        cargo = self._read_toml(pathlib.Path("Cargo.toml"))

        try:
            version = cargo["package"]["version"]  # type: ignore[index]
        except KeyError as exc:
            raise AutopubException("Cargo.toml must define package.version") from exc

        return str(version)

    def _update_cargo_version(self, version: str) -> None:
        cargo_path = pathlib.Path("Cargo.toml")
        cargo = self._read_toml(cargo_path)
        cargo["package"]["version"] = version  # type: ignore[index]
        self._write_toml(cargo_path, cargo)

    def post_check(self, release_info: ReleaseInfo) -> None:
        project_version = self._project_version()
        cargo_version = self._cargo_version()

        if project_version != cargo_version:
            raise AutopubException(
                "pyproject.toml project.version and Cargo.toml package.version "
                f"must match, got {project_version} and {cargo_version}"
            )

        if (
            release_info.previous_version
            and release_info.previous_version != cargo_version
        ):
            raise AutopubException(
                "AutoPub computed the previous version from pyproject.toml as "
                f"{release_info.previous_version}, but Cargo.toml has {cargo_version}"
            )

    def post_prepare(self, release_info: ReleaseInfo) -> None:
        if release_info.version is None:
            raise AutopubException("AutoPub did not compute a release version")

        self._update_cargo_version(release_info.version)
        subprocess.run(["cargo", "update", "--workspace", "--quiet"], check=True)
        subprocess.run(["uv", "lock"], check=True)

    def build(self) -> None:
        self.run_command([
            "uv",
            "run",
            "maturin",
            "build",
            "--release",
            "--out",
            "dist",
        ])

    def publish(self, repository: str | None = None, **kwargs: object) -> None:
        artifacts = sorted(
            path
            for path in pathlib.Path("dist").iterdir()
            if path.suffix == ".whl" or path.name.endswith(".tar.gz")
        )

        if not artifacts:
            raise AutopubException("No wheel or sdist artifacts found in dist/")

        command = ["uv", "publish", "--trusted-publishing", "always"]

        if repository:
            command.extend(["--index", repository])
        else:
            # Skip files already on PyPI so a retried release is idempotent
            # (a partial upload shouldn't block re-running the release).
            command.extend(["--check-url", "https://pypi.org/simple/"])

        command.extend(str(path) for path in artifacts)

        self.run_command(command)


def prepare_release() -> None:
    from autopub import Autopub
    from autopub.plugins.bump_version import BumpVersionPlugin
    from autopub.plugins.git import GitPlugin
    from autopub.plugins.update_changelog import UpdateChangelogPlugin

    autopub = Autopub(
        plugins=[
            GitPlugin,
            UpdateChangelogPlugin,
            BumpVersionPlugin,
            RignorePlugin,
        ]
    )
    autopub.validate_config()
    autopub.check()
    autopub.prepare()


if __name__ == "__main__":
    prepare_release()


__all__ = ["RignorePlugin"]
