import os
import subprocess
from pathlib import Path
import sys


def test_index_omits_github_badges_when_no_git_remote(tmp_path):
    """Run tools/gen_docs.py in an empty temp dir so no remote is found.
    Assert the generated index.md does not contain CI/Pages badge links.
    """
    out_dir = tmp_path / "docs_auto"
    out_dir.mkdir()

    # create a tiny emit script that prints a single node as JSON
    emit = tmp_path / "emit_node.py"
    emit.write_text(
        """
import json
nodes=[{"id":"n1","display_name":"One","type":"example","path":"one","description":"desc","tags":[]}]
print(json.dumps(nodes))
"""
    )

    script = Path('tools/gen_docs.py').resolve()
    # simulate no git repo by pointing GIT_DIR to an empty temp dir
    gitdir = tmp_path / 'nogit'
    gitdir.mkdir()
    env = os.environ.copy()
    env['GIT_DIR'] = str(gitdir)
    subprocess.check_call([sys.executable, str(script), '--emit-script', str(emit), '--out-dir', str(out_dir)], cwd=tmp_path, env=env)

    idx = out_dir / 'index.md'
    assert idx.exists(), "index.md was not generated"
    content = idx.read_text(encoding='utf-8')
    assert 'actions/workflows/ci.yml' not in content
    assert 'actions/workflows/deploy_pages.yml' not in content
