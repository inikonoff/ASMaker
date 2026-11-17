"""Запуск: страница открывается без ошибок, шаблон собирается, окно «Что нового» видят новые пользователи."""
from conftest import open_app


def test_opens_clean(app):
    assert app.js('doc.objects[0].type') == 'base'
    assert app.js('document.querySelector("#modal").hidden') is True


def test_whats_new_for_returning_user(browser, base_url):
    """Вернувшийся пользователь (видел прошлую версию) получает окно «Что нового», новичок — нет."""
    ctx = browser.new_context(); ctx.add_init_script("localStorage.setItem('stand-designer/v1:seen', JSON.stringify('2000-01-01'));")
    a = open_app(ctx.new_page(), base_url); a.wait(1200)
    assert 'Что нового' in a.js('document.querySelector("#modal").innerText')
    a.assert_clean(); ctx.close()
    ctx = browser.new_context(); a = open_app(ctx.new_page(), base_url); a.wait(1200)
    assert a.js('document.querySelector("#modal").hidden') is True
    a.assert_clean(); ctx.close()


def test_every_template_builds(app):
    n = app.js('BUILTIN_TPL.length')
    assert n >= 1
    for i in range(n):
        app.template(i)
        assert app.js('doc.objects.length') > 1, f'шаблон {i} пуст'
        assert app.js('document.querySelectorAll("#scene [data-id]").length') >= app.js('doc.objects.filter(o => o.visible && o.type !== "base").length') - 2
