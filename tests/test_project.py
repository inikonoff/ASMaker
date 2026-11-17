"""Данные проекта: нормализация устойчива, файл проекта читается обратно, старые проекты открываются."""
import json


def rich(app):
    app.template()
    app.js("""(() => { addPocket(); addText(); addShape('grad'); addPlate(); addDivider(); addItem('book'); addVar(); addPocket(); switchVar(0);
      mutate(null, () => { const t = doc.objects.find(o => o.type === 'text'); t.plate = normPlate({ style: 'petal', cor: 'in', corN: 3, edge: 'zig' }); }); })()""")


def test_normalize_is_idempotent(app):
    rich(app)
    a = app.js('JSON.stringify(normalize(JSON.parse(JSON.stringify(doc))))')
    b = app.js(f'JSON.stringify(normalize(JSON.parse({json.dumps(a)})))')
    assert a == b


def test_file_roundtrip(app):
    rich(app)
    norm = 'JSON.stringify(normalize(JSON.parse(JSON.stringify(doc))))'  # в памяти у шаблонных элементов может не быть полей по умолчанию
    before = app.js(norm)
    data = app.js('JSON.stringify(serialize())')
    app.js('newStand(true)'); app.wait(200)
    assert app.js(f'applyData(JSON.parse({json.dumps(data)}))') is True
    after = app.js(norm)
    if after != before:  # покажем первое расхождение по полям
        import json as J; a, b = J.loads(before), J.loads(after)
        diff = [(i, k, oa.get(k), ob.get(k)) for i, (oa, ob) in enumerate(zip(a['objects'], b['objects'])) for k in set(oa) | set(ob) if oa.get(k) != ob.get(k)]
        assert not diff, diff[:5]
        assert {k: v for k, v in a.items() if k != 'objects'} == {k: v for k, v in b.items() if k != 'objects'}


def test_old_project_without_new_fields(app):
    """Проект, сохранённый до появления новых полей (градиенты, плашки, изделия), открывается и дополняется значениями по умолчанию."""
    old = {'version': 4, 'title': 'Старый', 'objects': [
        {'id': 'b', 'type': 'base', 'name': 'База', 'x': 0, 'y': 0, 'w': 1000, 'h': 700, 'fillType': 'linear', 'fill': '#ffffff', 'fill2': '#000000'},
        {'id': 'p', 'type': 'pocket', 'name': 'Карман', 'x': 100, 'y': 100, 'fmt': 'A4'},
        {'id': 't', 'type': 'text', 'name': 'Текст', 'x': 10, 'y': 10, 'text': 'Привет', 'plate': {'style': 'round'}},
        {'id': 'i', 'type': 'item', 'name': 'Книга', 'x': 500, 'y': 100, 'kind': 'book'}]}
    n = app.js(f'normalize({json.dumps(old)})')
    assert n is not None
    b = n['objects'][0]
    assert b['fillA'] == 1 and b['mids'] == [] and b['rR'] == 71
    t = next(o for o in n['objects'] if o['type'] == 'text')
    assert t['plate']['cor'] == 'out' and t['plate']['fillOn'] is True
    assert app.js(f'applyData({{ doc: {json.dumps(old)} }})') is True


def test_garbage_is_rejected(app):
    for bad in ['null', '{}', '{"objects": 5}', '[1,2,3]']:
        assert not app.js(f'normalize({bad})')
