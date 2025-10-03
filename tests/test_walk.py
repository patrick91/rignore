from __future__ import annotations

from pathlib import Path

import pytest
from inline_snapshot import snapshot
from typing_extensions import LiteralString

import rignore

FOLDER_STRUCTURE = """
.hidden
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
    paths = [str(path.relative_to(folder)) for path in rignore.walk(folder)]

    assert paths == snapshot(
        [
            ".",
            "an_image.jpg",
            "some_file.txt",
            "some_folder",
            "some_folder/some_file.txt",
            "some_folder/some_folder",
            "some_folder/some_folder/some_file.txt",
        ]
    )


def test_filter_entry(folder: Path):
    def should_exclude(entry: Path) -> bool:
        return entry.name == "some_folder"

    paths = [
        str(path.relative_to(folder))
        for path in rignore.walk(folder, should_exclude_entry=should_exclude)
    ]

    assert paths == snapshot([".", "an_image.jpg", "some_file.txt"])


def test_overrides(folder: Path):
    paths = [
        str(path.relative_to(folder))
        for path in rignore.walk(folder, overrides=[".hidden"])
    ]

    assert paths == snapshot([".", ".hidden", "some_folder", "some_folder/some_folder"])
