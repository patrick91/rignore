use std::path::PathBuf;
use std::sync::Arc;

use ignore::overrides::OverrideBuilder;
use pyo3::prelude::*;

fn path_buf_to_pathlib_path(py: Python, path_buf: PathBuf) -> PyResult<Py<PyAny>> {
    let path_str = path_buf
        .to_str()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyValueError, _>("Invalid path"))?;

    let pathlib_module = py.import("pathlib")?;
    let path_class = pathlib_module.getattr("Path")?;
    let pathlib_path = path_class.call1((path_str,))?;

    Ok(pathlib_path.unbind())
}

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
        overrides=None,
        max_depth=None,
        max_filesize=None,
        follow_links=None,
        case_insensitive=None,
        same_file_system=None,
        should_exclude_entry=None,
    ))]
    fn new(
        path: PathBuf,

        ignore_hidden: Option<bool>,

        read_ignore_files: Option<bool>,
        read_parents_ignores: Option<bool>,

        read_git_ignore: Option<bool>,
        read_global_git_ignore: Option<bool>,
        read_git_exclude: Option<bool>,
        require_git: Option<bool>,

        additional_ignores: Option<Vec<String>>,
        additional_ignore_paths: Option<Vec<String>>,
        overrides: Option<Vec<String>>,

        max_depth: Option<usize>,
        max_filesize: Option<u64>,

        follow_links: Option<bool>,

        case_insensitive: Option<bool>,
        same_file_system: Option<bool>,
        should_exclude_entry: Option<Py<PyAny>>,
    ) -> Self {
        let mut builder = ignore::WalkBuilder::new(&path);

        // doing this at the beginning because otherwise it would override all the other options
        if let Some(override_patterns) = overrides {
            let mut override_builder = OverrideBuilder::new(&path);
            for pattern in override_patterns {
                let _ = override_builder.add(&pattern);
            }

            if let Ok(overrides) = override_builder.build() {
                builder.overrides(overrides);
            }
        }

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



        if let Some(filter_func) = should_exclude_entry {
            let filter = Arc::new(move |entry: &ignore::DirEntry| -> PyResult<bool> {
                Python::attach(|py| {
                    let path_buf = entry.path().to_path_buf();
                    let pathlib_path = path_buf_to_pathlib_path(py, path_buf)?;
                    let args = (pathlib_path,);
                    filter_func.call1(py, args)?.extract(py)
                })
            });

            builder.filter_entry(move |entry| {
                match filter(entry) {
                    Ok(result) => !result,
                    Err(e) => {
                        // Log the error or handle it as appropriate for your application
                        eprintln!("Error in filter function: {:?}", e);
                        false // Exclude the entry if there's an error
                    }
                }
            });
        }


        Walker(builder.build())
    }

    fn __iter__(slf: PyRef<Self>) -> PyResult<Py<Walker>> {
        Ok(slf.into())
    }

    fn __next__(mut slf: PyRefMut<Self>) -> PyResult<Option<Py<PyAny>>> {
        match slf.0.next() {
            Some(Ok(entry)) => {
                let path_buf = entry.path().to_path_buf();
                let pathlib_path = path_buf_to_pathlib_path(slf.py(), path_buf)?;

                Ok(Some(pathlib_path))
            }
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
    overrides=None,
    max_depth=None,
    max_filesize=None,
    follow_links=None,
    case_insensitive=None,
    same_file_system=None,
    should_exclude_entry=None,
))]
fn walk(
    path: PathBuf,

    ignore_hidden: Option<bool>,

    read_ignore_files: Option<bool>,
    read_parents_ignores: Option<bool>,

    read_git_ignore: Option<bool>,
    read_global_git_ignore: Option<bool>,
    read_git_exclude: Option<bool>,
    require_git: Option<bool>,

    additional_ignores: Option<Vec<String>>,
    additional_ignore_paths: Option<Vec<String>>,
    overrides: Option<Vec<String>>,

    max_depth: Option<usize>,
    max_filesize: Option<u64>,

    follow_links: Option<bool>,

    case_insensitive: Option<bool>,
    same_file_system: Option<bool>,

    should_exclude_entry: Option<Py<PyAny>>,
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
        overrides,
        max_depth,
        max_filesize,
        follow_links,
        case_insensitive,
        same_file_system,
        should_exclude_entry,
    ))
}

/// A Python module implemented in Rust.
#[pymodule(gil_used = false)]
fn rignore(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Walker>()?;
    m.add_function(wrap_pyfunction!(walk, m)?).unwrap();

    Ok(())
}
