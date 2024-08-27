from __future__ import annotations

from pathlib import Path

import pytest
from typing_extensions import LiteralString

import rignore

FOLDER_STRUCTURE = """
some_file.txt
some_folder/
some_folder/some_file.txt
some_folder/some_folder/
some_folder/some_folder/some_file.txt
an_image.jpg
""".strip()


@pytest.fixture
def folder_structure() -> list[LiteralString]:
    return FOLDER_STRUCTURE.splitlines()


@pytest.fixture
def folder(tmp_path: str, folder_structure: list[str]) -> Path:
    folder = Path(tmp_path)

    for path in folder_structure:
        if path.endswith("/"):
            (folder / path).mkdir()
        else:
            (folder / path).touch()

    return folder


def test_basic_walk(folder: Path, folder_structure: list[str]):
    paths = list(rignore.walk(folder))

    expected_paths = [folder] + [folder / path for path in folder_structure]

    assert len(paths) == 7

    for path in paths:
        assert path in expected_paths


def test_filter_entry(folder: Path):
    def should_exclude(entry: Path) -> bool:
        return entry.name == "some_folder"

    paths = list(rignore.walk(folder, should_exclude_entry=should_exclude))

    expected_paths = [
        folder,
        folder / "some_file.txt",
        folder / "an_image.jpg",
    ]

    assert len(paths) == 3

    for path in paths:
        assert path in expected_paths
