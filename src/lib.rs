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
        ignore_hidden=true,
        read_ignore_files=true,
        read_parents_ignores=true,
        read_git_ignore=true,
        read_global_git_ignore=true,
        read_git_exclude=true,
        require_git=false,
        additional_ignores=vec![],
        additional_ignore_paths=vec![],
        overrides=vec![],
        max_depth=None,
        max_filesize=None,
        follow_links=false,
        case_insensitive=false,
        same_file_system=false,
        should_exclude_entry=None,
    ))]
    fn new(
        path: PathBuf,

        ignore_hidden: bool,

        read_ignore_files: bool,
        read_parents_ignores: bool,

        read_git_ignore: bool,
        read_global_git_ignore: bool,
        read_git_exclude: bool,
        require_git: bool,

        additional_ignores: Vec<String>,
        additional_ignore_paths: Vec<String>,
        overrides: Vec<String>,

        max_depth: Option<usize>,
        max_filesize: Option<u64>,

        follow_links: bool,

        case_insensitive: bool,
        same_file_system: bool,
        should_exclude_entry: Option<Py<PyAny>>,
    ) -> Self {
        let mut builder = ignore::WalkBuilder::new(&path);

        // doing this at the beginning because otherwise it would override all the other options
        if !overrides.is_empty() {
            let mut override_builder = OverrideBuilder::new(&path);
            for pattern in overrides {
                let _ = override_builder.add(&pattern);
            }

            if let Ok(overrides) = override_builder.build() {
                builder.overrides(overrides);
            }
        }

        builder.hidden(ignore_hidden);
        builder.follow_links(follow_links);

        builder.max_depth(max_depth);
        builder.max_filesize(max_filesize);

        builder.ignore(read_ignore_files);

        for pattern in additional_ignores {
            builder.add_ignore(pattern);
        }

        for path in additional_ignore_paths {
            builder.add_custom_ignore_filename(path);
        }

        builder.parents(read_parents_ignores);
        builder.git_global(read_global_git_ignore);
        builder.git_ignore(read_git_ignore);
        builder.git_exclude(read_git_exclude);
        builder.require_git(require_git);
        builder.ignore_case_insensitive(case_insensitive);
        builder.same_file_system(same_file_system);



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
    ignore_hidden=true,
    read_ignore_files=true,
    read_parents_ignores=true,
    read_git_ignore=true,
    read_global_git_ignore=true,
    read_git_exclude=true,
    require_git=false,
    additional_ignores=vec![],
    additional_ignore_paths=vec![],
    overrides=vec![],
    max_depth=None,
    max_filesize=None,
    follow_links=false,
    case_insensitive=false,
    same_file_system=false,
    should_exclude_entry=None,
))]
fn walk(
    path: PathBuf,

    ignore_hidden: bool,

    read_ignore_files: bool,
    read_parents_ignores: bool,

    read_git_ignore: bool,
    read_global_git_ignore: bool,
    read_git_exclude: bool,
    require_git: bool,

    additional_ignores: Vec<String>,
    additional_ignore_paths: Vec<String>,
    overrides: Vec<String>,

    max_depth: Option<usize>,
    max_filesize: Option<u64>,

    follow_links: bool,

    case_insensitive: bool,
    same_file_system: bool,

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
