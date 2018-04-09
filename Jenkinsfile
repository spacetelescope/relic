// Obtain files from source control system.
if (utils.scm_checkout()) return

// Globals
CONDA_CREATE = "conda create -y -q"
PY_SETUP = "python setup.py"
PYTEST_ARGS = "-v --junitxml results.xml"

matrix_python = ["2.7", "3.5", "3.6"]
matrix = []

// RUN ONCE:
//    "sdist" is agnostic enough to work without any dependencies
sdist = new BuildConfig()
sdist.nodetype = "linux-stable"
sdist.build_mode = "sdist"
sdist.build_cmds = ["${PY_SETUP} sdist"]
matrix += sdist

// Generate compatibility matrix
for (python_ver in matrix_python) {
    DEPS = "python=${python_ver} pytest git"
    CENV = "py${python_ver}"

    install = new BuildConfig()
    install.nodetype = "linux-stable"
    install.build_mode = CENV
    install.build_cmds = ["${CONDA_CREATE} -n ${CENV} ${DEPS}",
                          "with_env -n ${CENV} ${PY_SETUP} egg_info",
                          "with_env -n ${CENV} ${PY_SETUP} install"]
    install.test_cmds = ["with_env -n ${CENV} pytest ${PYTEST_ARGS}"]
    matrix += install
}

// Iterate over configurations that define the (distibuted) build matrix.
// Spawn a host of the given nodetype for each combination and run in parallel.
utils.run(matrix)
