"""Картинки: переживают перезапуск вкладки, в т. ч. сразу после правки; лишние удаляются из хранилища."""

ADD_IMG = """(async (n) => { const ids = [];
  for (let k = 0; k < n; k++) {
    const cv = document.createElement('canvas'); cv.width = 3000; cv.height = 2200; const x = cv.getContext('2d');
    for (let i = 0; i < 4000; i++) { x.fillStyle = `hsl(${Math.random() * 360},70%,50%)`; x.fillRect(Math.random() * 3000, Math.random() * 2200, 50, 50); }
    addShape('empty'); const id = sel, a = 'a' + uid(); assets[a] = cv.toDataURL('image/jpeg', 0.95);
    mutate(null, () => { byId(id).image = { asset: a, x: 0, y: 0, w: 300, h: 220, opacity: 1, fit: 'cover' }; }); ids.push(a);
  } return ids; })"""
SHOWN = "doc.objects.filter(o => o.image && assets[o.image.asset]).length"


def test_images_survive_quick_close(profile):
    """Регрессия 17.11.2026: фото больше квоты localStorage пропадали, если вкладку закрыть сразу после правки."""
    a = profile
    a.template()
    a.js(ADD_IMG + '(3)'); a.wait(4000)
    assert a.js('Object.values(assets).reduce((s, d) => s + d.length, 0)') > 5e6, 'фото должны превышать квоту автосохранения'
    a.js('mutate(null, () => { doc.objects.find(o => o.image).x += 5; })'); a.wait(100)
    a.reload()
    assert a.js(SHOWN) == 3
    a.reload()
    assert a.js(SHOWN) == 3


def test_canvas_uses_blob_urls_and_export_uses_data(profile):
    a = profile
    a.template(); a.js(ADD_IMG + '(1)'); a.wait(500)
    hrefs = a.js('[...document.querySelectorAll("#scene image")].map(i => i.getAttribute("href")).filter(Boolean).map(h => h.slice(0, 5))')
    assert hrefs and all(h == 'blob:' for h in hrefs)
    assert 'href="data:image/jpeg' in a.js('exportSVG(400, 300)')


def test_unused_images_are_collected(profile):
    a = profile
    a.template(); (k1,) = a.js(ADD_IMG + '(1)'); a.wait(2500); p1 = a.js('pid')
    a.js('newStand(true)'); a.wait(300); (k2,) = a.js(ADD_IMG + '(1)'); a.wait(2500)
    a.js(f"projects.del('{p1}')"); a.js('gcAssets()'); a.wait(300)
    keys = a.js('assetDB.keys()')
    assert k1 not in keys and k2 in keys
