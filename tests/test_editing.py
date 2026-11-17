"""Правка: добавление элементов, отмена и повтор, группы, копирование стиля, свой размер изделий."""

ADD_ALL = """(() => { addPocket(); addText(); addShape('grad'); addShape('empty'); addPlate(); addDivider();
  for (const k of Object.keys(ITEM_KINDS)) addItem(k); return doc.objects.length; })()"""


def test_add_every_kind_and_undo(app):
    app.template()
    n0 = app.js('doc.objects.length')
    n1 = app.js(ADD_ALL); app.wait(300)
    assert n1 > n0 + 6
    kinds = set(app.js('doc.objects.map(o => o.type)'))
    assert {'pocket', 'text', 'shape', 'divider', 'item'} <= kinds
    for _ in range(n1 - n0): app.js('undo()')
    assert app.js('doc.objects.length') == n0
    app.js('redo()'); assert app.js('doc.objects.length') == n0 + 1


def test_typing_merges_into_one_undo_step(app):
    app.template()
    app.js("addText()"); n = app.js('past.length')
    for t in ['А', 'Аб', 'Абв']: app.js(f"mutate('txt', () => byId(sel).text = '{t}')")
    assert app.js('past.length') == n + 1


def test_group_and_ungroup(app):
    app.template()
    ids = app.js("doc.objects.filter(o => o.type === 'pocket').slice(0, 2).map(o => o.id)")
    app.js(f'setSel({ids}); groupSel()')
    assert app.js('doc.groups.length') == 1
    app.js('ungroupSel()'); assert app.js('doc.groups.length') == 0


def test_copy_paste_style_between_shapes(app):
    app.template()
    app.js("addShape('grad'); mutate(null, () => { const o = byId(sel); o.fill = '#123456'; o.mids = [{ id: 'm1', c: '#ff0000', a: 0.5, p: 0.4 }]; })")
    app.js("copyStyle(); addShape('solid'); pasteStyle()")
    o = app.js('byId(sel)')
    assert o['fill'] == '#123456' and o['mids'][0]['c'] == '#ff0000'


def test_item_custom_size(app):
    app.template()
    app.js("addItem('cards')")
    std = app.js('[byId(sel).w, byId(sel).h]')
    app.js("mutate(null, () => { const o = byId(sel); o.custom = true; o.lw = 210; o.lh = 56; })")
    assert app.js('cardStacks(byId(sel))') == 2
    assert 'свой размер' in app.js('itemParams(byId(sel))')
    app.js("mutate(null, () => { byId(sel).custom = false; })")
    assert app.js('[byId(sel).w, byId(sel).h]') == std


def test_split_switches_to_production_view(app):
    app.template()
    app.js("setViewMode('client'); select(base().id); addSplit()"); app.wait(300)
    assert app.js('view_.mode') == 'prod'
    assert app.js('document.querySelectorAll(".split-line").length') >= 1


def test_variants(app):
    app.template()
    app.js('addVar()'); app.js("addPocket()"); n1 = app.js('doc.objects.length')
    app.js('switchVar(0)'); n0 = app.js('doc.objects.length')
    assert n1 == n0 + 1
    app.js('switchVar(1)'); assert app.js('doc.objects.length') == n1
    app.js('void deleteVar(1)'); app.page.click('.ask-wrap button:has-text("Удалить")'); app.wait(200); assert app.js('doc.vars == null || doc.vars.names.length === 1')
