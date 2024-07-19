from typing import Optional, List, Callable, Iterator

class Walker:
    def __init__(
        self,
        path: str,
        ignore_hidden: Optional[bool] = None,
        read_ignore_files: Optional[bool] = None,
        read_parents_ignores: Optional[bool] = None,
        read_git_ignore: Optional[bool] = None,
        read_global_git_ignore: Optional[bool] = None,
        read_git_exclude: Optional[bool] = None,
        require_git: Optional[bool] = None,
        additional_ignores: Optional[List[str]] = None,
        additional_ignore_paths: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
        max_filesize: Optional[int] = None,
        follow_links: Optional[bool] = None,
        case_insensitive: Optional[bool] = None,
        same_file_system: Optional[bool] = None,
        filter_entry: Optional[Callable[[str], bool]] = None,
    ) -> None: ...
    def __iter__(self) -> Iterator[str]: ...
    def __next__(self) -> Optional[str]: ...

def walk(
    path: str,
    ignore_hidden: Optional[bool] = None,
    read_ignore_files: Optional[bool] = None,
    read_parents_ignores: Optional[bool] = None,
    read_git_ignore: Optional[bool] = None,
    read_global_git_ignore: Optional[bool] = None,
    read_git_exclude: Optional[bool] = None,
    require_git: Optional[bool] = None,
    additional_ignores: Optional[List[str]] = None,
    additional_ignore_paths: Optional[List[str]] = None,
    max_depth: Optional[int] = None,
    max_filesize: Optional[int] = None,
    follow_links: Optional[bool] = None,
    case_insensitive: Optional[bool] = None,
    same_file_system: Optional[bool] = None,
    filter_entry: Optional[Callable[[str], bool]] = None,
) -> Walker: ...
