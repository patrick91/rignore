from __future__ import annotations

from pathlib import Path
from typing_extensions import LiteralString

import rignore
import pytest


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
    paths = list(rignore.walk(str(folder)))

    expected_paths = [str(folder)] + [str(folder / path) for path in folder_structure]

    assert len(paths) == 7

    for path in paths:
        assert path in expected_paths
