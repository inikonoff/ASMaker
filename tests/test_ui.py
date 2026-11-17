"""Интерфейс: панель свойств каждого элемента на каждой вкладке, список слоёв, подсказки, линейка."""


def test_props_for_every_type_and_tab(app):
    app.template()
    app.js("(() => { addPocket(); addText(); addShape('grad'); addPlate(); addDivider(); for (const k of Object.keys(ITEM_KINDS)) addItem(k); })()")
    ids = app.js('doc.objects.map(o => o.id)')
    tabs = app.js('TABS.map(t => t[0])')
    for i in ids + [None]:
        app.js(f'select({"null" if i is None else repr(i)}); flush()')
        for t in tabs:
            app.js(f'setPropsTab({t!r}); flush()')
    app.js('setSel(doc.objects.filter(o => o.type === "pocket").map(o => o.id)); flush()')
    assert app.js('document.querySelector("#propsPane").childElementCount') > 0


def test_layer_list_follows_selection(app):
    app.template()
    app.js('for (let i = 0; i < 30; i++) addPocket()'); app.wait(200)
    app.js("select(doc.objects.find(o => o.type === 'pocket').id)"); app.wait(400)
    inside = app.js("""(() => { const l = $('#layerList'), r = l.querySelector(`[data-lid="${sel}"]`).getBoundingClientRect(), b = l.getBoundingClientRect();
      return r.top >= b.top - 1 && r.bottom <= b.bottom + 1; })()""")
    assert inside


def test_layer_rows_are_reused(app):
    app.template()
    app.js("window.__row = $('#layerList').lastElementChild; mutate(null, () => doc.title = 'Другое'); flush()")
    assert app.js("$('#layerList').lastElementChild === window.__row")


def test_marquee_shows_size(app):
    app.template(); app.js('select(null)')
    p = app.page; p.mouse.move(300, 150); p.mouse.down(); p.mouse.move(500, 260, steps=6); app.wait(100)
    assert '×' in app.js("document.querySelector('.ruler-txt')?.textContent || ''")
    p.mouse.up()


def test_name_tip(app):
    app.template(); app.js('select(null)')
    x, y, name = app.js("""(() => { const o = doc.objects.find(o => o.type === 'pocket'); const r = document.querySelector(`#scene [data-id="${o.id}"]`).getBoundingClientRect();
      return [r.x + r.width / 2, r.y + r.height / 2 + 30, o.name]; })()""")
    app.page.mouse.move(x, y); app.page.mouse.move(x + 2, y + 2); app.wait(1300)
    assert app.js('nameTip.hidden') is False and app.js('nameTip.textContent') == name
