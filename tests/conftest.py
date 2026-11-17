"""Общая обвязка тестов ASMaker.

Тесты открывают собранный index.html в настоящем браузере (Playwright, Chromium)
через локальный http-сервер и проверяют поведение через страницу: функции
приложения доступны из window, поэтому тест может и кликать, и вызывать их напрямую.

    pip install pytest playwright && python -m playwright install chromium
    python -m pytest tests -q

Переменные окружения:
    CHROME   путь к своему Chrome/Chromium (если браузер Playwright не установлен)
"""
import functools, http.server, os, re, shutil, socketserver, tempfile, threading
import pytest
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# окно «Что нового» не должно мешать: помечаем последнюю запись прочитанной
WHATS_KEY = re.search(r"const WHATS_NEW = \[\s*\{ v: '([^']+)'", open(os.path.join(ROOT, 'src', 'app.html'), encoding='utf-8').read()).group(1)
SEEN = f"localStorage.setItem('stand-designer/v1:seen', JSON.stringify('{WHATS_KEY}'));"
# шум, не относящийся к приложению: недоступный в песочнице вход Google и т.п.
NOISE = ('accounts.google', 'apis.google', 'gstatic', 'Failed to load resource', 'agent-proxy', 'ERR_')


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


@pytest.fixture(scope='session')
def base_url():
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=ROOT))
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{srv.server_address[1]}/index.html'
    srv.shutdown()


@pytest.fixture(scope='session')
def pw():
    with sync_playwright() as p:
        yield p


def launch_opts():
    o = {'args': ['--no-sandbox']}
    if os.environ.get('CHROME'): o['executable_path'] = os.environ['CHROME']
    return o


@pytest.fixture(scope='session')
def browser(pw):
    b = pw.chromium.launch(**launch_opts())
    yield b
    b.close()


class App:
    """Страница приложения + собранные ошибки. app.js(...) — выполнить код в странице."""
    def __init__(self, page):
        self.page, self.errors = page, []
        page.on('pageerror', lambda e: self.errors.append(f'pageerror: {e}'))
        page.on('console', lambda m: m.type == 'error' and not any(n in m.text for n in NOISE) and self.errors.append(f'console: {m.text}'))

    def js(self, code, arg=None):
        return self.page.evaluate(code, arg) if arg is not None else self.page.evaluate(code)

    def wait(self, ms=200):
        self.page.wait_for_timeout(ms)

    def template(self, i=0):
        """Открыть встроенный шаблон — типичный стенд с подложкой, заголовком и карманами."""
        self.js(f'newFromBuiltin(BUILTIN_TPL[{i}])'); self.wait(500)

    def assert_clean(self):
        assert not self.errors, '\n'.join(self.errors)


def open_app(page, url):
    app = App(page)
    page.goto(url); page.wait_for_function('typeof doc === "object" && typeof flush === "function"'); app.wait(300)
    return app


@pytest.fixture
def app(browser, base_url):
    ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(SEEN)
    a = open_app(ctx.new_page(), base_url)
    yield a
    errs = list(a.errors); ctx.close()
    assert not errs, 'Ошибки в странице:\n' + '\n'.join(errs)


@pytest.fixture
def profile(pw, base_url):
    """Постоянный профиль браузера: для проверок, переживает ли проект перезапуск вкладки."""
    d = tempfile.mkdtemp(prefix='asm-prof-')
    ctx = pw.chromium.launch_persistent_context(d, viewport={'width': 1440, 'height': 900}, **launch_opts())
    ctx.add_init_script(SEEN)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    a = open_app(page, base_url)
    a.reload = lambda: (page.reload(), page.wait_for_function('typeof doc === "object"'), a.wait(2500))
    yield a
    errs = list(a.errors); ctx.close(); shutil.rmtree(d, ignore_errors=True)
    assert not errs, 'Ошибки в странице:\n' + '\n'.join(errs)
