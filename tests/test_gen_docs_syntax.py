import py_compile


def test_gen_docs_compiles():
    """Ensure tools/gen_docs.py compiles (catches SyntaxError regressions)."""
    py_compile.compile("tools/gen_docs.py", doraise=True)
