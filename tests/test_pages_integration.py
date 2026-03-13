import os
import sys
import json
import subprocess
import tempfile
import shutil
import pytest


def test_build_mkdocs_site(tmp_path, monkeypatch):
    # create a simple emit_node that returns one node
    node = {
        "id": "int::node/1",
        "type": "function",
        "display_name": "Integration Node",
        "path": "examples/prototype/skills/test.py",
        "description": "Integration test node",
    }

    emit = tmp_path / "emit_node.py"
    emit.write_text("import json\nprint(json.dumps(%s))\n" % json.dumps(node))

    env = os.environ.copy()
    env["EMIT_SCRIPT"] = str(emit)

    # run the generator
    subprocess.check_call([sys.executable, os.path.join("tools", "gen_docs.py")], env=env)

    # skip if mkdocs not installed
    pytest.importorskip('mkdocs')

    site_dir = os.path.join(os.getcwd(), 'site')
    # clean site dir
    if os.path.exists(site_dir):
        shutil.rmtree(site_dir)

    # build site using mkdocs CLI
    res = subprocess.run([sys.executable, '-m', 'mkdocs', 'build', '--site-dir', site_dir], capture_output=True)
    assert res.returncode == 0, res.stderr.decode('utf-8')

    # basic check for index.html
    index = os.path.join(site_dir, 'index.html')
    assert os.path.exists(index), 'MkDocs site build did not produce index.html'
