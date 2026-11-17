"""Сборка: index.html собран из текущего src/app.html, встроенный код без синтаксических ошибок."""
import os, re, shutil, subprocess, sys, tempfile
import pytest
from conftest import ROOT

sys.path.insert(0, os.path.join(ROOT, 'tools'))
from build import src_hash  # noqa: E402


def test_index_built_from_current_source():
    src = open(os.path.join(ROOT, 'src', 'app.html'), encoding='utf-8').read()
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    m = re.search(r'<!-- src-sha256: (\w+) -->', html)
    assert m, 'в index.html нет отпечатка — соберите: python3 tools/build.py'
    assert m.group(1) == src_hash(src), 'index.html устарел — соберите заново: python3 tools/build.py'


@pytest.mark.skipif(not shutil.which('node'), reason='нужен node')
def test_inline_scripts_parse():
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    scripts = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', html, re.S)
    assert scripts
    for i, code in enumerate(scripts):
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f: f.write(code)
        r = subprocess.run(['node', '--check', f.name], capture_output=True, text=True); os.unlink(f.name)
        assert r.returncode == 0, f'скрипт {i}: {r.stderr[:500]}'
