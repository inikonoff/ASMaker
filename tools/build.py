#!/usr/bin/env python3
"""Собирает index.html: встраивает кириллические шрифты в src/app.html.

Шрифты скачиваются из npm (пакеты Fontsource, лицензия SIL OFL) в кэш build/
и вставляются в страницу как base64, поэтому готовый index.html работает
офлайн одним файлом.

    python3 tools/build.py
"""
import base64, glob, json, os, re, subprocess, sys, tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'build', 'fonts')
FONTS = [  # подпись, npm-пакет, имя семейства в CSS, какие файлы брать
    ('Inter', '@fontsource-variable/inter', 'Inter Variable', r'inter-(cyrillic|latin)-wght-(normal|italic)'),
    ('Roboto', '@fontsource-variable/roboto', 'Roboto Variable', r'roboto-(cyrillic|latin)-wght-(normal|italic)'),
    ('Montserrat', '@fontsource-variable/montserrat', 'Montserrat Variable', r'montserrat-(cyrillic|latin)-wght-(normal|italic)'),
    ('PT Sans', '@fontsource/pt-sans', 'PT Sans', r'pt-sans-(cyrillic|latin)-(400|700)-(normal|italic)'),
    ('PT Serif', '@fontsource/pt-serif', 'PT Serif', r'pt-serif-(cyrillic|latin)-(400|700)-(normal|italic)'),
    ('Playfair Display', '@fontsource-variable/playfair-display', 'Playfair Display Variable', r'playfair-display-(cyrillic|latin)-wght-(normal|italic)'),
    ('Oswald', '@fontsource-variable/oswald', 'Oswald Variable', r'oswald-(cyrillic|latin)-wght-normal'),
    ('Rubik', '@fontsource-variable/rubik', 'Rubik Variable', r'rubik-(cyrillic|latin)-wght-(normal|italic)'),
    ('Comfortaa', '@fontsource-variable/comfortaa', 'Comfortaa Variable', r'comfortaa-(cyrillic|latin)-wght-normal'),
    ('Lobster', '@fontsource/lobster', 'Lobster', r'lobster-(cyrillic|latin)-400-normal'),
    ('Caveat', '@fontsource-variable/caveat', 'Caveat Variable', r'caveat-(cyrillic|latin)-wght-normal'),
    ('Russo One', '@fontsource/russo-one', 'Russo One', r'russo-one-(cyrillic|latin)-400-normal'),
]


def fetch(pkg):
    """Скачивает и распаковывает npm-пакет в кэш, возвращает путь к package/."""
    dest = os.path.join(CACHE, pkg.replace('@', '').replace('/', '-'))
    if not os.path.isdir(os.path.join(dest, 'package')):
        os.makedirs(dest, exist_ok=True)
        tgz = subprocess.run(['npm', 'pack', pkg, '--silent', '--pack-destination', dest],
                             check=True, capture_output=True, text=True).stdout.strip().splitlines()[-1]
        with tarfile.open(os.path.join(dest, tgz)) as t:
            t.extractall(dest, filter='data')
    return os.path.join(dest, 'package')


def font_db():
    db, data = [], {}
    for label, pkg, css, pat in FONTS:
        root, faces = fetch(pkg), {}
        for cf in glob.glob(root + '/*.css'):
            for blk in re.findall(r'@font-face\s*{[^}]*}', open(cf, encoding='utf-8').read()):
                m, rg = re.search(r'files/([\w-]+)\.woff2', blk), re.search(r'unicode-range:\s*([^;]+);', blk)
                if not m or not rg or not re.fullmatch(pat, m.group(1)) or m.group(1) in faces:
                    continue
                fn = m.group(1)
                faces[fn] = {'file': fn, 'style': re.search(r'font-style:\s*(\w+)', blk).group(1),
                             'weight': re.search(r'font-weight:\s*([\d ]+);', blk).group(1).strip(), 'range': rg.group(1).strip()}
                data[fn] = base64.b64encode(open(f'{root}/files/{fn}.woff2', 'rb').read()).decode()
        ws = [int(x) for f in faces.values() for x in f['weight'].split()]
        db.append({'label': label, 'css': css, 'wmin': min(ws), 'wmax': max(ws),
                   'italic': any(f['style'] == 'italic' for f in faces.values()),
                   'static': not pkg.startswith('@fontsource-variable/'), 'faces': list(faces.values())})
        print(f'  {label}: {len(faces)} файлов', file=sys.stderr)
    return db, data


def main():
    src = open(os.path.join(ROOT, 'src', 'app.html'), encoding='utf-8').read()
    assert src.count('/*FONTS*/') == 1, 'в src/app.html должна быть ровно одна метка /*FONTS*/'
    db, data = font_db()
    js = 'const FONT_DB = ' + json.dumps(db, ensure_ascii=False) + ';\nconst FONT_DATA = ' + json.dumps(data) + ';\n'
    out = os.path.join(ROOT, 'index.html')
    open(out, 'w', encoding='utf-8').write(src.replace('/*FONTS*/', js))
    print(f'index.html: {os.path.getsize(out) / 1e6:.1f} МБ', file=sys.stderr)


if __name__ == '__main__':
    main()
