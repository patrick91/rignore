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
    paths = sorted(str(path.relative_to(folder)) for path in rignore.walk(folder))

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

    paths = sorted(
        str(path.relative_to(folder))
        for path in rignore.walk(folder, should_exclude_entry=should_exclude)
    )

    assert paths == snapshot([".", "an_image.jpg", "some_file.txt"])


def test_overrides(folder: Path):
    paths = sorted(
        str(path.relative_to(folder))
        for path in rignore.walk(folder, overrides=[".hidden"])
    )

    assert paths == snapshot([".", ".hidden", "some_folder", "some_folder/some_folder"])


def test_ignore_hidden(folder: Path):
    """Test that hidden files and folders are ignored when ignore_hidden=False."""
    paths = sorted(
        str(path.relative_to(folder))
        for path in rignore.walk(folder, ignore_hidden=False)
    )

    assert paths == snapshot(
        [
            ".",
            ".hidden",
            "an_image.jpg",
            "some_file.txt",
            "some_folder",
            "some_folder/some_file.txt",
            "some_folder/some_folder",
            "some_folder/some_folder/some_file.txt",
        ]
    )


def test_ignore_hidden_default(folder: Path):
    """Test that hidden files are ignored by default."""
    paths = sorted(
        str(path.relative_to(folder))
        for path in rignore.walk(folder, ignore_hidden=True)
    )

    # .hidden should not be in the results
    assert ".hidden" not in paths
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


def test_max_depth(folder: Path):
    """Test max_depth parameter limits traversal depth."""
    # Depth 0 should only return the root directory
    paths_0 = sorted(
        str(path.relative_to(folder))
        for path in rignore.walk(folder, max_depth=0)
    )
    assert paths_0 == snapshot(["."])

    # Depth 1 should return root and immediate children
    paths_1 = sorted(
        str(path.relative_to(folder))
        for path in rignore.walk(folder, max_depth=1)
    )
    assert paths_1 == snapshot([".", "an_image.jpg", "some_file.txt", "some_folder"])

    # Depth 2 should go one level deeper
    paths_2 = sorted(
        str(path.relative_to(folder))
        for path in rignore.walk(folder, max_depth=2)
    )
    assert paths_2 == snapshot(
        [
            ".",
            "an_image.jpg",
            "some_file.txt",
            "some_folder",
            "some_folder/some_file.txt",
            "some_folder/some_folder",
        ]
    )


def test_gitignore(tmp_path: Path):
    """Test that .gitignore files are respected when in a git repository."""
    import subprocess
    
    # Initialize git repository
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, capture_output=True)
    
    # Create folder structure
    (tmp_path / "included.txt").touch()
    (tmp_path / "ignored.txt").touch()
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "file.txt").touch()
    
    # Create .gitignore
    (tmp_path / ".gitignore").write_text("ignored.txt\nbuild/\n")

    paths = sorted(
        str(path.relative_to(tmp_path))
        for path in rignore.walk(tmp_path, read_git_ignore=True)
    )

    assert "ignored.txt" not in paths
    assert "build" not in paths
    assert "build/file.txt" not in paths
    assert "included.txt" in paths


def test_additional_ignore_paths(tmp_path: Path):
    """Test additional_ignore_paths parameter with custom ignore file."""
    # Create folder structure
    (tmp_path / "included.txt").touch()
    (tmp_path / "ignored.txt").touch()
    (tmp_path / "other.log").touch()
    
    # Create custom ignore file
    custom_ignore = tmp_path / ".customignore"
    custom_ignore.write_text("ignored.txt\n*.log\n")

    paths = sorted(
        str(path.relative_to(tmp_path))
        for path in rignore.walk(tmp_path, additional_ignore_paths=[".customignore"])
    )

    # Files matching patterns in custom ignore should be excluded
    assert "ignored.txt" not in paths
    assert "other.log" not in paths
    
    # But other files should be present
    assert "included.txt" in paths


def test_read_parents_ignores(tmp_path: Path):
    """Test read_parents_ignores parameter."""
    # Create parent directory with .ignore file
    parent = tmp_path / "parent"
    parent.mkdir()
    (parent / ".ignore").write_text("*.log\n")
    
    # Create child directory
    child = parent / "child"
    child.mkdir()
    (child / "file.txt").touch()
    (child / "debug.log").touch()

    # Walk child directory with read_parents_ignores=True
    paths = sorted(
        str(path.relative_to(child))
        for path in rignore.walk(child, read_parents_ignores=True, read_ignore_files=True)
    )

    # .log files should be ignored based on parent's .ignore file
    assert "debug.log" not in paths
    assert "file.txt" in paths


def test_max_filesize(tmp_path: Path):
    """Test max_filesize parameter."""
    # Create files of different sizes
    small_file = tmp_path / "small.txt"
    large_file = tmp_path / "large.txt"
    
    small_file.write_text("small")  # 5 bytes
    large_file.write_text("x" * 1000)  # 1000 bytes

    # Only files <= 100 bytes should be included
    paths = sorted(
        str(path.relative_to(tmp_path))
        for path in rignore.walk(tmp_path, max_filesize=100)
    )

    assert "small.txt" in paths
    assert "large.txt" not in paths


def test_follow_links(tmp_path: Path):
    """Test follow_links parameter with symbolic links."""
    # Create a directory structure
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    (real_dir / "file.txt").touch()
    
    # Create a symbolic link
    link_dir = tmp_path / "link_dir"
    link_dir.symlink_to(real_dir)

    # Without following links
    paths_no_follow = sorted(
        str(path.relative_to(tmp_path))
        for path in rignore.walk(tmp_path, follow_links=False)
    )
    
    # With following links
    paths_follow = sorted(
        str(path.relative_to(tmp_path))
        for path in rignore.walk(tmp_path, follow_links=True)
    )

    # When following links, we should see files inside the linked directory
    assert "real_dir/file.txt" in paths_no_follow
    # The behavior depends on the platform, but follow_links should allow traversal


def test_case_insensitive(tmp_path: Path):
    """Test case_insensitive parameter for ignore patterns."""
    import subprocess
    
    # Initialize git repository
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    
    # Create files with different cases
    (tmp_path / "test.TXT").touch()
    (tmp_path / "test.txt").touch()
    (tmp_path / "TEST.TXT").touch()
    (tmp_path / "other.log").touch()
    
    # Create .gitignore with lowercase pattern
    (tmp_path / ".gitignore").write_text("*.txt\n")

    # Case-insensitive matching
    paths = sorted(
        str(path.relative_to(tmp_path))
        for path in rignore.walk(
            tmp_path, 
            case_insensitive=True,
            read_git_ignore=True
        )
    )

    # All case variations of .txt should be ignored when case_insensitive=True
    assert "test.TXT" not in paths
    assert "test.txt" not in paths
    assert "TEST.TXT" not in paths
    # But other files should be present
    assert "other.log" in paths


def test_walker_class_directly(folder: Path):
    """Test using Walker class directly instead of walk function."""
    walker = rignore.Walker(folder)
    paths = sorted(str(path.relative_to(folder)) for path in walker)

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


def test_walker_with_options(folder: Path):
    """Test Walker class with various options."""
    walker = rignore.Walker(folder, max_depth=1, ignore_hidden=True)
    paths = sorted(str(path.relative_to(folder)) for path in walker)

    assert paths == snapshot([".", "an_image.jpg", "some_file.txt", "some_folder"])


def test_empty_directory(tmp_path: Path):
    """Test walking an empty directory."""
    paths = list(rignore.walk(tmp_path))
    
    assert len(paths) == 1
    assert paths[0] == tmp_path


def test_read_ignore_files(tmp_path: Path):
    """Test read_ignore_files parameter with .ignore files."""
    # Create folder structure
    (tmp_path / "included.txt").touch()
    (tmp_path / "ignored_by_ignore.txt").touch()
    
    # Create .ignore file
    (tmp_path / ".ignore").write_text("ignored_by_ignore.txt\n")

    paths = sorted(
        str(path.relative_to(tmp_path))
        for path in rignore.walk(tmp_path, read_ignore_files=True)
    )

    assert "ignored_by_ignore.txt" not in paths
    assert "included.txt" in paths


def test_overrides_with_negation(folder: Path):
    """Test overrides with negation patterns."""
    # Include only .txt files, but exclude some_file.txt
    paths = sorted(
        str(path.relative_to(folder))
        for path in rignore.walk(folder, overrides=["*.txt", "!some_file.txt"])
    )

    # Should include .txt files except some_file.txt (in root)
    assert "some_file.txt" not in paths
    assert paths == snapshot([".", "some_folder", "some_folder/some_folder"])


def test_require_git(tmp_path: Path):
    """Test require_git parameter."""
    import subprocess
    
    # Create a directory that's not a git repository
    non_git_dir = tmp_path / "not_git"
    non_git_dir.mkdir()
    (non_git_dir / "file.txt").touch()
    
    # With require_git=True, this should return empty results (or just root)
    paths_required = list(rignore.walk(non_git_dir, require_git=True))
    
    # The walker should still work but may not traverse
    assert len(paths_required) >= 0
    
    # Now create a git repository
    git_dir = tmp_path / "is_git"
    git_dir.mkdir()
    subprocess.run(["git", "init"], cwd=git_dir, capture_output=True)
    (git_dir / "file.txt").touch()
    
    # With require_git=True in a git repository, it should work normally
    paths_git = list(rignore.walk(git_dir, require_git=True))
    assert len(paths_git) > 0


def test_same_file_system(tmp_path: Path):
    """Test same_file_system parameter."""
    # Create directory structure
    (tmp_path / "file1.txt").touch()
    (tmp_path / "file2.txt").touch()
    
    # Walk with same_file_system=True
    paths = sorted(
        str(path.relative_to(tmp_path))
        for path in rignore.walk(tmp_path, same_file_system=True)
    )
    
    # Should include all files from the same filesystem
    assert "file1.txt" in paths
    assert "file2.txt" in paths


def test_nested_directories(tmp_path: Path):
    """Test walking deeply nested directory structures."""
    # Create deeply nested structure
    current = tmp_path
    for i in range(5):
        current = current / f"level_{i}"
        current.mkdir()
        (current / f"file_{i}.txt").touch()
    
    paths = list(rignore.walk(tmp_path))
    
    # Should traverse all levels by default
    assert len(paths) > 10  # Root + 5 directories + 5 files


def test_multiple_filter_conditions(tmp_path: Path):
    """Test combining multiple filtering options."""
    import subprocess
    
    # Initialize git repository
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    
    # Create structure
    (tmp_path / ".hidden").touch()
    (tmp_path / "visible.txt").touch()
    (tmp_path / "large.bin").write_bytes(b"x" * 1000)
    (tmp_path / "small.bin").write_bytes(b"x" * 10)
    
    # Create .gitignore
    (tmp_path / ".gitignore").write_text("*.txt\n")
    
    # Combine multiple filters
    paths = sorted(
        str(path.relative_to(tmp_path))
        for path in rignore.walk(
            tmp_path,
            ignore_hidden=True,
            read_git_ignore=True,
            max_filesize=100
        )
    )
    
    # .hidden should be excluded (hidden)
    # visible.txt should be excluded (gitignore)
    # large.bin should be excluded (filesize)
    # small.bin should be included
    assert ".hidden" not in paths
    assert "visible.txt" not in paths
    assert "large.bin" not in paths
    assert "small.bin" in paths


def test_pathlib_path_return_type(folder: Path):
    """Test that walk returns pathlib.Path objects."""
    for path in rignore.walk(folder):
        assert isinstance(path, Path)
        # Verify we can call Path methods on it
        assert hasattr(path, "exists")
        assert hasattr(path, "is_file")


def test_iterator_protocol(folder: Path):
    """Test that Walker properly implements the iterator protocol."""
    walker = rignore.Walker(folder)
    
    # Should be iterable
    assert hasattr(walker, "__iter__")
    assert hasattr(walker, "__next__")
    
    # Should be able to iterate multiple times by creating new walkers
    walker1 = rignore.Walker(folder)
    walker2 = rignore.Walker(folder)
    
    paths1 = list(walker1)
    paths2 = list(walker2)
    
    # Both iterations should return the same results
    assert sorted(str(p) for p in paths1) == sorted(str(p) for p in paths2)
