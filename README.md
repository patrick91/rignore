# rignore 🚀🐍

`rignore` is a Python module that provides a high-performance, Rust-powered file system traversal functionality. It wraps the Rust `ignore` crate using PyO3, offering an efficient way to walk through directories while respecting various ignore rules.

## ✨ Features

- 🚀 Fast directory traversal powered by Rust
- 🙈 Respects `.gitignore` rules
- 🛠️ Customizable ignore patterns
- 💾 Efficient memory usage
- 🐍 Easy-to-use Python API

## 📦 Installation

You can install `rignore` using pip:

```bash
pip install rignore
```

## 🚀 Usage

The main function provided by `rignore` is `walk`, which returns an iterator of file paths:

```python
import rignore

for file_path in rignore.walk("/path/to/directory"):
    print(file_path)
```

### 🔧 Advanced Usage

The `walk` function accepts several optional parameters to customize its behavior:

```python
rignore.walk(
    path,
    ignore_hidden=True,
    read_ignore_files=True,
    read_parents_ignores=True,
    read_git_ignore=True,
    read_global_git_ignore=True,
    read_git_exclude=True,
    require_git=False,
    additional_ignores=(),
    additional_ignore_paths=(),
    overrides=(),
    max_depth=None,
    max_filesize=None,
    follow_links=False,
    case_insensitive=False,
    same_file_system=False,
    filter_entry=None,
)
```

#### 📝 Parameters

- `path` (str): The root directory to start the walk from.
- `ignore_hidden` (bool, optional): Whether to ignore hidden files and directories.
- `read_ignore_files` (bool, optional): Whether to read `.ignore` files.
- `read_parents_ignores` (bool, optional): Whether to read ignore files from parent directories.
- `read_git_ignore` (bool, optional): Whether to respect `.gitignore` files.
- `read_global_git_ignore` (bool, optional): Whether to respect global Git ignore rules.
- `read_git_exclude` (bool, optional): Whether to respect Git exclude files.
- `require_git` (bool, optional): Whether to require the directory to be a Git repository.
- `additional_ignores` (List[str], optional): Additional ignore patterns to apply.
- `additional_ignore_paths` (List[str], optional): Additional ignore file paths to read.
- `overrides` (List[str], optional): Override globs with the same semantics as gitignore. Globs provided here are treated as whitelist matches, meaning only files matching these patterns will be included. Use `!` at the beginning of a glob to exclude files (e.g., `["*.txt", ".env.example", "!secret.txt"]` will include all `.txt` files and `.env.example`, but exclude `secret.txt`).
- `max_depth` (int, optional): Maximum depth to traverse.
- `max_filesize` (int, optional): Maximum file size to consider (in bytes).
- `follow_links` (bool, optional): Whether to follow symbolic links.
- `case_insensitive` (bool, optional): Whether to use case-insensitive matching for ignore patterns.
- `same_file_system` (bool, optional): Whether to stay on the same file system.
- `filter_entry` (Callable[[str, bool], optional): Custom filter function to exclude entries.

## ⚡ Performance

`rignore` leverages the power of Rust to provide high-performance directory traversal. It's significantly faster than pure Python implementations, especially for large directory structures.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [ignore](https://github.com/BurntSushi/ripgrep/tree/master/crates/ignore) - The Rust crate that powers this project
- [PyO3](https://github.com/PyO3/pyo3) - The library used to create Python bindings for Rust code
