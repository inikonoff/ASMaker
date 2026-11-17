"""Экспорт: SVG, PNG, PDF, чертёж и пакет для цеха собираются и имеют правильный формат."""
import base64, io, zipfile

CATCH = """window.__dl = []; window.download = async (blob, name) => { const b = new Uint8Array(await blob.arrayBuffer());
  let s = ''; for (let i = 0; i < b.length; i += 0x8000) s += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000));
  window.__dl.push({ name, size: blob.size, b64: btoa(s) }); return true; }; 0"""


def files(app, timeout=60000):
    app.page.wait_for_function('window.__dl && window.__dl.length', timeout=timeout)
    return [(f['name'], base64.b64decode(f['b64'])) for f in app.js('window.__dl')]


def test_svg_export_is_valid_xml(app):
    app.template()
    s = app.js('exportSVG(800, 600)')
    assert s.startswith('<svg') and app.js("s => !new DOMParser().parseFromString(s, 'image/svg+xml').querySelector('parsererror')", s)


def test_png_and_pdf(app):
    app.template(); app.js(CATCH)
    app.js('exportPNG()')
    (name, data), = files(app)
    assert name.endswith('.png') and data[:8] == b'\x89PNG\r\n\x1a\n'
    app.js('window.__dl = []; exportDrawing()')
    (name, data), = files(app)
    assert name.endswith('чертёж.pdf') and data[:5] == b'%PDF-' and data.rstrip().endswith(b'%%EOF')


def test_workshop_pack(app):
    app.template(); app.js(CATCH)
    app.js("Object.assign(expOpts, { fmt: 'tif', dpi: 50 }); select(base().id); addSplit()")
    app.js('runWorkPack()')
    (name, data), = files(app, 120000)
    assert name.endswith('для цеха.zip')
    z = zipfile.ZipFile(io.BytesIO(data)); names = z.namelist()
    assert any(n.endswith('чертёж.pdf') for n in names)
    tifs = [n for n in names if n.endswith('.tif')]
    assert len(tifs) == 2 and all(z.read(n)[:4] in (b'II*\x00', b'MM\x00*') for n in tifs)


def test_variants_pdf(app):
    app.template(); app.js(CATCH); app.js('addVar()')
    app.js('exportVariantsPDF()')
    (name, data), = files(app)
    assert data[:5] == b'%PDF-' and data.count(b'/Type /Page') - data.count(b'/Type /Pages') == 2
