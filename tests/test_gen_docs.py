import os
import sys
import json
import subprocess


def test_gen_docs_creates_markdown(tmp_path, monkeypatch):
    node = {
        "id": "test::node/1",
        "type": "function",
        "display_name": "Test: Node",
        "path": "examples/prototype/skills/test.py",
        "description": "A short description for testing.",
        "tags": ["fast", "unit"],
        "canonical_url": "https://example.com/test-node"
    }

    emit = tmp_path / "emit_node.py"
    emit.write_text("import json\nprint(json.dumps(%s))\n" % json.dumps(node))

    env = os.environ.copy()
    env["EMIT_SCRIPT"] = str(emit)

    # run the generator script
    subprocess.check_call([sys.executable, os.path.join("tools", "gen_docs.py")], env=env)

    out_dir = os.path.join(os.getcwd(), "docs", "auto")
    filename = node["id"].replace("::", "__").replace("/", "_") + ".md"
    path = os.path.join(out_dir, filename)

    assert os.path.exists(path), f"Expected generated file at {path}"
    text = open(path, encoding="utf-8").read()
    assert text.startswith("---"), "Front matter missing"
    assert 'display_name:' in text
    assert 'description' in text
    assert 'fast' in text
    assert 'canonical_url' in text
    assert '# Test: Node' in text
