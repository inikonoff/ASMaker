"""Отрисовка: все виды плашек, разделителей, изделий, наполнений и градиентов дают корректную разметку."""
import pytest


def svg_ok(app, markup):
    return app.js("m => { const d = new DOMParser().parseFromString(`<svg xmlns='http://www.w3.org/2000/svg'>${m}</svg>`, 'image/svg+xml'); return !d.querySelector('parsererror') && !/NaN|undefined/.test(m); }", markup)


def test_every_plate_style(app):
    app.template()
    styles = app.js('PLATE_STYLES.map(s => s[0]).filter(s => s !== "none")')
    for st in styles:
        for extra in ['{}', "{cor:'in',corN:4,edge:'out'}", "{cor:'out',corN:3,edge:'zig',edgeS:'v',fillOn:false}", "{border:'double',orn:'flower'}"]:
            m = app.js(f"(() => {{ addText(); const o = byId(sel); mutate(null, () => {{ o.text = 'Раздел\\nвторая строка'; o.plate = normPlate({{ style: '{st}', ...{extra} }}); }}); return objMarkup(byId(sel), true); }})()")
            assert svg_ok(app, m), f'плашка {st} {extra}'


def test_every_divider(app):
    app.template()
    for st in app.js('DIV_STYLES.map(s => s[0])'):
        for cap in app.js('DIV_CAPS.map(s => s[0])'):
            m = app.js(f"(() => {{ const o = makeDivider(); o.style = '{st}'; o.cap = '{cap}'; o.ornN = 3; return dividerMarkup(o, true); }})()")
            assert svg_ok(app, m), f'разделитель {st}/{cap}'


def test_every_item_and_fill(app):
    app.template()
    for k in app.js('Object.keys(ITEM_KINDS)'):
        app.js(f"addItem('{k}')"); assert svg_ok(app, app.js('objMarkup(byId(sel), true)')), k
    for f in app.js('FILL_KEYS'):
        app.js(f"addPocket(); mutate(null, () => byId(sel).fill = '{f}')")
        assert svg_ok(app, app.js('objMarkup(byId(sel), true)')), f


@pytest.mark.parametrize('kind', ['linear', 'radial'])
def test_gradient_stops(app, kind):
    app.template()
    app.js(f"addShape('grad'); mutate(null, () => {{ const o = byId(sel); o.fillType = '{kind}'; o.fillA = 0; o.mids = [{{ id: 'a', c: '#ff0000', a: 0.5, p: 0.3 }}, {{ id: 'b', c: '#00ff00', a: 1, p: 0.7 }}]; }})")
    m = app.js('objMarkup(byId(sel), true)')
    assert svg_ok(app, m) and m.count('<stop') == 4 and 'stop-opacity="0"' in m


@pytest.mark.parametrize('mode', ['prod', 'client'])
def test_scene_in_both_views(app, mode):
    app.template()
    app.js("(() => { addPocket(); addText(); addShape('grad'); addPlate(); addDivider(); addItem('flip'); })()")
    app.js(f"setViewMode('{mode}'); invalidate('all'); flush()")
    assert app.js('document.querySelectorAll("#scene [data-id]").length') >= 6
