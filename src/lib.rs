use std::sync::Arc;

use pyo3::prelude::*;

#[pyclass]
pub struct Walker(ignore::Walk);

#[pymethods]
impl Walker {
    #[new]
    #[pyo3(signature = (
        path,
        ignore_hidden=None,
        read_ignore_files=None,
        read_parents_ignores=None,
        read_git_ignore=None,
        read_global_git_ignore=None,
        read_git_exclude=None,
        require_git=None,
        additional_ignores=None,
        additional_ignore_paths=None,
        max_depth=None,
        max_filesize=None,
        follow_links=None,
        case_insensitive=None,
        same_file_system=None,
        filter_entry=None,
    ))]
    fn new(
        path: &str,

        ignore_hidden: Option<bool>,

        read_ignore_files: Option<bool>,
        read_parents_ignores: Option<bool>,

        read_git_ignore: Option<bool>,
        read_global_git_ignore: Option<bool>,
        read_git_exclude: Option<bool>,
        require_git: Option<bool>,

        additional_ignores: Option<Vec<String>>,
        additional_ignore_paths: Option<Vec<String>>,

        max_depth: Option<usize>,
        max_filesize: Option<u64>,

        follow_links: Option<bool>,

        case_insensitive: Option<bool>,
        same_file_system: Option<bool>,
        filter_entry: Option<PyObject>,
    ) -> Self {
        let mut builder = ignore::WalkBuilder::new(path);

        if let Some(ignore_hidden) = ignore_hidden {
            builder.hidden(ignore_hidden);
        }

        if let Some(follow_links) = follow_links {
            builder.follow_links(follow_links);
        }

        builder.max_depth(max_depth);
        builder.max_filesize(max_filesize);

        if let Some(read_ignore_files) = read_ignore_files {
            builder.ignore(read_ignore_files);
        }

        if let Some(additional_ignores) = additional_ignores {
            for pattern in additional_ignores {
                builder.add_ignore(pattern);
            }
        }

        if let Some(additional_ignore_paths) = additional_ignore_paths {
            for path in additional_ignore_paths {
                builder.add_custom_ignore_filename(path);
            }
        }

        if let Some(read_parents_ignores) = read_parents_ignores {
            builder.parents(read_parents_ignores);
        }

        if let Some(read_global_git_ignore) = read_global_git_ignore {
            builder.git_global(read_global_git_ignore);
        }

        if let Some(read_git_ignore) = read_git_ignore {
            builder.git_ignore(read_git_ignore);
        }

        if let Some(read_git_exclude) = read_git_exclude {
            builder.git_exclude(read_git_exclude);
        }

        if let Some(require_git) = require_git {
            builder.require_git(require_git);
        }

        if let Some(case_insensitive) = case_insensitive {
            builder.ignore_case_insensitive(case_insensitive);
        }

        if let Some(same_file_system) = same_file_system {
            builder.same_file_system(same_file_system);
        }

        if let Some(filter_func) = filter_entry {
            let filter = Arc::new(move |entry: &ignore::DirEntry| -> bool {
                Python::with_gil(|py| {
                    let args = (entry.path().display().to_string(),);
                    match filter_func.call1(py, args) {
                        Ok(result) => result.extract(py).unwrap_or(true),
                        Err(_) => true,
                    }
                })
            });
            builder.filter_entry(move |entry| filter(entry));
        }

        Walker(builder.build())
    }

    fn __iter__(slf: PyRef<Self>) -> PyResult<Py<Walker>> {
        Ok(slf.into())
    }

    fn __next__(mut slf: PyRefMut<Self>) -> PyResult<Option<String>> {
        match slf.0.next() {
            Some(Ok(entry)) => Ok(Some(entry.path().display().to_string())),
            Some(Err(err)) => Err(PyErr::new::<pyo3::exceptions::PyOSError, _>(format!(
                "{}",
                err
            ))),
            None => Ok(None),
        }
    }
}

#[pyfunction]
#[pyo3(signature = (
    path,
    ignore_hidden=None,
    read_ignore_files=None,
    read_parents_ignores=None,
    read_git_ignore=None,
    read_global_git_ignore=None,
    read_git_exclude=None,
    require_git=None,
    additional_ignores=None,
    additional_ignore_paths=None,
    max_depth=None,
    max_filesize=None,
    follow_links=None,
    case_insensitive=None,
    same_file_system=None,
    filter_entry=None,
))]
fn walk(
    // same as walker::new
    path: &str,

    ignore_hidden: Option<bool>,

    read_ignore_files: Option<bool>,
    read_parents_ignores: Option<bool>,

    read_git_ignore: Option<bool>,
    read_global_git_ignore: Option<bool>,
    read_git_exclude: Option<bool>,
    require_git: Option<bool>,

    additional_ignores: Option<Vec<String>>,
    additional_ignore_paths: Option<Vec<String>>,

    max_depth: Option<usize>,
    max_filesize: Option<u64>,

    follow_links: Option<bool>,

    case_insensitive: Option<bool>,
    same_file_system: Option<bool>,

    filter_entry: Option<PyObject>,
) -> PyResult<Walker> {
    Ok(Walker::new(
        path,
        ignore_hidden,
        read_ignore_files,
        read_parents_ignores,
        read_git_ignore,
        read_global_git_ignore,
        read_git_exclude,
        require_git,
        additional_ignores,
        additional_ignore_paths,
        max_depth,
        max_filesize,
        follow_links,
        case_insensitive,
        same_file_system,
        filter_entry,
    ))
}

/// A Python module implemented in Rust.
#[pymodule]
fn rignore(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Walker>()?;
    m.add_function(wrap_pyfunction!(walk, m)?).unwrap();

    Ok(())
}
