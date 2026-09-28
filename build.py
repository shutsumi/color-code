#!/usr/bin/env python3
"""日本の色のページ一式を data/wairo.json から生成する。

    python3 build.py

生成するもの
- wairo/index.html          … 日本の色の一覧ページ
- wairo/<slug>/index.html   … 1色ごとのページ
- sitemap.xml
- index.html の <!--WAIRO-DATA--> と <!--CONSULT--> の間（和色データと相談ボタン）
"""
import html, json, math, re
from pathlib import Path

# ---- 設定 ----
SITE = 'https://shutsumi.github.io/color-code/'
FORM_URL = ''  # 相談用GoogleフォームのURL。空のあいだは相談ボタンを出さない
TODAY = '2026-09-28'

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / 'data/wairo.json').read_text(encoding='utf-8'))
COLORS = DATA['colors']
YURAI = json.loads((ROOT / 'data/yurai.json').read_text(encoding='utf-8'))  # 名前の由来（自前の文章）
esc = html.escape

# ---- ひらがな → ローマ字（URL用） ----
KANA = dict(zip(
    'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんがぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽぁぃぅぇぉ',
    'a i u e o ka ki ku ke ko sa shi su se so ta chi tsu te to na ni nu ne no ha hi fu he ho ma mi mu me mo ya yu yo ra ri ru re ro wa o n ga gi gu ge go za ji zu ze zo da ji zu de do ba bi bu be bo pa pi pu pe po a i u e o'.split()))
YOON = {'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo'}

def romaji(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        nxt = s[i + 1] if i + 1 < len(s) else ''
        if c == 'っ':
            out.append('__sokuon__'); i += 1; continue
        if nxt in YOON and c in KANA:
            base = KANA[c]
            if base in ('shi', 'chi', 'ji'):
                out.append(base[:-1] + YOON[nxt][1:])  # しゃ→sha、ちょ→cho、じゅ→ju
            else:
                out.append(base[:-1] + YOON[nxt])      # きゃ→kya
            i += 2; continue
        out.append(KANA.get(c, '')); i += 1
    s = ''.join(out)
    return re.sub(r'__sokuon__(.)', lambda m: ('t' if m.group(1) == 'c' else m.group(1)) + m.group(1), s)

# ---- 色の計算 ----
def rgb(hx): return [int(hx[i:i + 2], 16) for i in (0, 2, 4)]
def hexs(c): return ''.join(f'{max(0, min(255, round(x))):02X}' for x in c)

def hsl(c):
    r, g, b = [x / 255 for x in c]
    mx, mn = max(r, g, b), min(r, g, b); d = mx - mn; l = (mx + mn) / 2
    h = 0
    if d:
        h = ((g - b) / d) % 6 if mx == r else (b - r) / d + 2 if mx == g else (r - g) / d + 4
    s = d / (1 - abs(2 * l - 1)) if d else 0
    return (h * 60) % 360, s, l

def lin(v):
    v /= 255
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def lab(c):
    r, g, b = map(lin, c)
    x = (r * .4124 + g * .3576 + b * .1805) / .95047
    y = (r * .2126 + g * .7152 + b * .0722)
    z = (r * .0193 + g * .1192 + b * .9505) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)

def de(a, b): return math.dist(a, b)

def luminance(c):
    r, g, b = map(lin, c)
    return .2126 * r + .7152 * g + .0722 * b

def contrast(a, b):
    la, lb = sorted((a, b), reverse=True)
    return (la + .05) / (lb + .05)

FAMILIES = [('red', '赤'), ('pink', 'ピンク'), ('orange', '橙・オレンジ'), ('brown', '茶'), ('yellow', '黄'),
            ('green', '緑'), ('blue', '青'), ('purple', '紫'), ('mono', '白・灰・黒')]

def family(c):
    L, a, b = lab(c)
    if math.hypot(a, b) < 5:
        return 'mono'
    h, s, l = hsl(c)
    if h >= 345 or h < 12:
        return 'pink' if l > .75 else 'red'
    if h < 42:
        return 'brown' if l < .42 or (s < .45 and l < .6) else 'orange'
    if h < 65:
        return 'brown' if l < .35 or (s < .5 and l < .45) else 'yellow'
    if h < 170: return 'green'
    if h < 228: return 'blue'
    if h < 290: return 'purple'
    if h < 320: return 'pink' if l > .55 else 'purple'
    return 'pink' if l > .55 else 'red'

def tone(c):
    L, a, b = lab(c)
    C = math.hypot(a, b)
    if C < 5:
        return '白に近い' if L > 90 else '黒に近い' if L < 22 else '明るい灰色の' if L > 62 else '灰色の' if L > 40 else '暗い灰色の'
    light = ('とても明るく' if L >= 85 else '明るく' if L >= 65 else '中くらいの明るさで' if L >= 45 else '暗めで' if L >= 28 else 'とても暗く')
    chroma = ('鮮やかな' if C >= 60 else 'はっきりした' if C >= 35 else '落ち着いた' if C >= 18 else 'くすんだ')
    return f'{light}{chroma}'

for e in COLORS:
    e['rgb'] = rgb(e['hex']); e['lab'] = lab(e['rgb']); e['family'] = family(e['rgb'])
    e['reading'] = e['readings'][0]

# URL（ローマ字の読み。重複したら色番号を足す）
used = {}
for e in COLORS:
    s = romaji(e['reading'])
    used[s] = used.get(s, 0) + 1
for e in COLORS:
    s = romaji(e['reading'])
    e['slug'] = s if used[s] == 1 else f"{s}-{e['hex'].lower()}"
assert len({e['slug'] for e in COLORS}) == len(COLORS)

FAM_LABEL = dict(FAMILIES)

# ---- 共通パーツ ----
def consult(prefix):
    if not FORM_URL:
        return ''
    return f'''<section class="consult">
      <p>ツールへのご要望や、お仕事のご相談はこちらから</p>
      <a class="consult-btn" href="{esc(FORM_URL)}" target="_blank" rel="noopener">このツールの製作者に相談する</a>
    </section>'''

def head(title, desc, url, prefix, theme='#ffffff', extra=''):
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">
<meta name="theme-color" content="{theme}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="カラーコードをクリックでコピー">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}ogp.png">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap">
<link rel="stylesheet" href="{prefix}assets/sub.css">
{extra}</head>
<body>
<div class="wrap">
'''

def foot(prefix):
    return f'''  <footer>
    {consult(prefix)}
    <p>色の名前・読み・カラーコードは、Wikipedia「<a href="https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC%E3%81%AE%E8%89%B2%E3%81%AE%E4%B8%80%E8%A6%A7" target="_blank" rel="noopener">日本の色の一覧</a>」に載っている近似値です。同じ名前の色でも、資料によってカラーコードが少しずつ違うことがあります。</p>
    <p><a href="{prefix}">カラーコードをクリックでコピー</a>｜<a href="{prefix}wairo/">日本の色の一覧</a></p>
  </footer>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"><i></i><span></span></div>
<script src="{prefix}assets/sub.js"></script>
</body>
</html>
'''

def breadcrumb_ld(items):
    return '<script type="application/ld+json">' + json.dumps({
        '@context': 'https://schema.org', '@type': 'BreadcrumbList',
        'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(items)]
    }, ensure_ascii=False) + '</script>\n'

def copybtn(label, text, hx, cls='cp'):
    return f'<button class="{cls}" type="button" data-copy="{esc(text)}" data-hex="{hx}"><b>{label}</b><code>{esc(text)}</code></button>'

def mini(e, prefix, note=''):
    return (f'<a class="mini" href="{prefix}wairo/{e["slug"]}/"><i style="background:#{e["hex"]}"></i>'
            f'<span>{esc(e["name"])}<code>#{e["hex"]}</code>{f"<small>{note}</small>" if note else ""}</span></a>')

# ---- 1色ごとのページ ----
def color_page(idx, e):
    P = '../../'
    c, hx = e['rgb'], e['hex']
    h, s, l = hsl(c)
    name, rd = e['name'], e['reading']
    url = f"{SITE}wairo/{e['slug']}/"
    alias = '・'.join(e['aliases'])
    other_reads = '・'.join(e['readings'][1:])
    fam = FAM_LABEL[e['family']]
    lum = luminance(c)
    cw, cb = contrast(lum, 1.0), contrast(lum, 0.0)
    best, ratio = ('白', cw) if cw >= cb else ('黒', cb)
    ink = '#ffffff' if cw >= cb else '#222222'
    readable = ('Webの読みやすさの目安（4.5:1）を満たしているので、本文の文字にも使えます。' if ratio >= 4.5
                else '大きめの見出しや太字なら読みやすく、細い本文の文字にはやや不向きです。' if ratio >= 3
                else 'どちらの文字でも差が小さいので、文字を重ねるなら濃い縁取りや別の地色を使うのがおすすめです。')
    same = [o for o in COLORS if o is not e and o['hex'] == hx]
    near = sorted((o for o in COLORS if o['hex'] != hx), key=lambda o: de(o['lab'], e['lab']))[:8]
    prev_e, next_e = COLORS[idx - 1], COLORS[(idx + 1) % len(COLORS)]

    steps = []
    for t in (0.8, 0.6, 0.4, 0.2):
        steps.append(('薄い', hexs([x + (255 - x) * t for x in c])))
    steps.append(('元の色', hx))
    for t in (0.2, 0.4, 0.6):
        steps.append(('濃い', hexs([x * (1 - t) for x in c])))

    title = f'{name}（{rd}）のカラーコード #{hx}｜色番号・RGB'
    desc = (f'{name}（{rd}）のカラーコード（色番号・カラーナンバー）は #{hx}、RGBは({c[0]}, {c[1]}, {c[2]})です。'
            f'{YURAI[name]}#付き・#なしの6桁やRGBをクリックでコピーできます。')
    alias_txt = f'<p>別の書き方：{esc(alias)}</p>' if alias else ''
    reads_txt = f'「{esc(other_reads)}」とも読みます。' if other_reads else ''
    same_txt = ''
    if same:
        same_txt = ('<p class="note">同じカラーコードで載っている色：' +
                    '、'.join(f'<a href="{P}wairo/{o["slug"]}/">{esc(o["name"])}</a>' for o in same) + '</p>')

    body = f'''  <nav class="crumb" aria-label="パンくずリスト"><a href="{P}">カラーコードをクリックでコピー</a> › <a href="{P}wairo/">日本の色</a> › <span>{esc(name)}</span></nav>
  <main class="stack">
    <header class="hero" style="background:#{hx};color:{ink}">
      <p class="yomi">{esc(rd)}</p>
      <h1>{esc(name)}のカラーコード</h1>
      <p class="hx">#{hx}</p>
      <p class="yurai">{esc(YURAI[name])}</p>
    </header>

    <section class="stack-s">
      <p class="lead"><strong>{esc(name)}（{esc(rd)}）</strong>のカラーコード（色番号・カラーナンバー）は <strong class="num">#{hx}</strong>（「#」シャープつきの6桁の番号）です。RGBでは赤{c[0]}・緑{c[1]}・青{c[2]}。{esc(name)}は、{tone(c)}{fam}系の色です。{reads_txt}</p>
      {alias_txt}
      <div class="cps">
        {copybtn('#つき', '#' + hx, hx)}
        {copybtn('#なし', hx, hx)}
        {copybtn('RGB', f'rgb({c[0]}, {c[1]}, {c[2]})', hx)}
        {copybtn('HSL', f'hsl({round(h)}, {round(s * 100)}%, {round(l * 100)}%)', hx)}
      </div>
      <p class="note">クリックするとコピーされます。CanvaやPowerPointには「#なし」、HTMLやCSSには「#つき」が便利です。</p>
      {same_txt}
    </section>

    <section class="stack-s">
      <h2>{esc(name)}を使うときの目安</h2>
      <div class="demo">
        <div style="background:#{hx};color:#ffffff">白い文字<span class="num">{cw:.1f}:1</span></div>
        <div style="background:#{hx};color:#222222">黒い文字<span class="num">{cb:.1f}:1</span></div>
      </div>
      <p>{esc(name)}の上に文字をのせるなら、<strong>{best}い文字</strong>のほうが読みやすくなります（コントラスト比 {ratio:.1f}:1）。{readable}</p>
      <h3>HTML・CSSでの書き方</h3>
      <pre><code>color: #{hx};            /* 文字を{esc(name)}にする */
background-color: #{hx}; /* 背景を{esc(name)}にする */</code></pre>
    </section>

    <section class="stack-s">
      <h2>{esc(name)}の薄い色・濃い色</h2>
      <p class="note">白や黒を混ぜた色です。クリックでカラーコードをコピーできます。</p>
      <div class="steps">
        {''.join(f'<button type="button" data-copy="#{sx}" data-hex="{sx}" class="{"on" if lab_ == "元の色" else ""}" style="background:#{sx}" aria-label="{lab_} #{sx} をコピー"><span style="color:{"#222" if luminance(rgb(sx)) > .35 else "#fff"}">#{sx}</span></button>' for lab_, sx in steps)}
      </div>
      <div class="steps-l"><span>薄い</span><span>濃い</span></div>
    </section>

    <section class="stack-s">
      <h2>{esc(name)}に似ている日本の色</h2>
      <div class="minis">{''.join(mini(o, P) for o in near)}</div>
    </section>

    <nav class="pager" aria-label="前後の色">
      <a href="{P}wairo/{prev_e["slug"]}/">‹ {esc(prev_e["name"])}</a>
      <a href="{P}wairo/">日本の色の一覧</a>
      <a href="{P}wairo/{next_e["slug"]}/">{esc(next_e["name"])} ›</a>
    </nav>

    <a class="cta" href="{P}">全色マップから、ほかのカラーコードを探す</a>
  </main>
'''
    ld = breadcrumb_ld([('カラーコードをクリックでコピー', SITE), ('日本の色', SITE + 'wairo/'), (name, url)])
    return head(title, desc, url, P, '#' + hx, ld) + body + foot(P)

# ---- 一覧ページ ----
def index_page():
    P = '../'
    url = SITE + 'wairo/'
    title = f'日本の色（和色）のカラーコード一覧 {len(COLORS)}色｜名前・読み方・色番号'
    desc = (f'東雲色・山吹色・藍色など、日本の伝統的な色の名前{len(COLORS)}色のカラーコード（色番号）と読み方の一覧。'
            'クリックで#つきの6桁をコピーできます。色名や読み方で検索もできます。')
    groups = []
    for key, label in FAMILIES:
        items = sorted((e for e in COLORS if e['family'] == key), key=lambda e: (-e['lab'][0]))
        if not items: continue
        cards = ''.join(
            f'<li class="card" data-q="{esc(" ".join([e["name"], *e["aliases"], *e["readings"], e["hex"]]))}">'
            f'<a href="{e["slug"]}/"><i style="background:#{e["hex"]}"></i><span><b>{esc(e["name"])}</b><small>{esc(e["reading"])}</small></span></a>'
            f'<button type="button" data-copy="#{e["hex"]}" data-hex="{e["hex"]}" aria-label="{esc(e["name"])} #{e["hex"]} をコピー"><code>#{e["hex"]}</code></button></li>'
            for e in items)
        groups.append(f'<section class="fam" id="{key}"><h2><i style="background:#{items[len(items) // 2]["hex"]}"></i>{label}系の色 <small>{len(items)}色</small></h2><ul class="cards">{cards}</ul></section>')
    famnav = ''.join(f'<a href="#{k}">{l}</a>' for k, l in FAMILIES)
    body = f'''  <nav class="crumb" aria-label="パンくずリスト"><a href="{P}">カラーコードをクリックでコピー</a> › <span>日本の色</span></nav>
  <main class="stack">
    <header class="stack-s">
      <h1 class="plain">日本の色の名前とカラーコード一覧</h1>
      <p class="lead">東雲色（しののめいろ）、山吹色（やまぶきいろ）、藍色（あいいろ）など、日本で使われてきた色の名前{len(COLORS)}色のカラーコード（色番号）をまとめました。色番号をクリックすると「#」つきの6桁がコピーされます。色の名前を押すと、RGBや似ている色がわかる専用ページが開きます。</p>
    </header>
    <div class="filter">
      <input id="q" class="field" type="search" placeholder="色の名前・読み方・カラーコードで探す（例 やまぶき）" aria-label="色を探す">
      <nav class="famnav" aria-label="系統">{famnav}</nav>
    </div>
    <p class="note" id="none" hidden>見つかりませんでした。ひらがなや別の書き方でも探してみてください。</p>
    {''.join(groups)}
    <a class="cta" href="{P}">全色マップから、ほかのカラーコードを探す</a>
  </main>
'''
    ld = breadcrumb_ld([('カラーコードをクリックでコピー', SITE), ('日本の色', url)])
    return head(title, desc, url, P, '#ffffff', ld) + body + foot(P)

# ---- 書き出し ----
def main():
    out = ROOT / 'wairo'
    for i, e in enumerate(COLORS):
        d = out / e['slug']; d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(color_page(i, e), encoding='utf-8')
    (out / 'index.html').write_text(index_page(), encoding='utf-8')
    # 使われなくなったページを消す
    slugs = {e['slug'] for e in COLORS}
    for d in out.iterdir():
        if d.is_dir() and d.name not in slugs:
            for f in d.iterdir(): f.unlink()
            d.rmdir()

    urls = [SITE, SITE + 'wairo/'] + [f"{SITE}wairo/{e['slug']}/" for e in COLORS]
    (ROOT / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        ''.join(f'  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in urls) + '</urlset>\n', encoding='utf-8')

    # トップページに和色データと相談ボタンを差し込む
    idx = ROOT / 'index.html'
    s = idx.read_text(encoding='utf-8')
    data = [[e['name'], e['reading'], e['hex'], e['slug']] for e in COLORS]
    s = re.sub(r'(<!--WAIRO-DATA-->).*?(<!--/WAIRO-DATA-->)',
               lambda m: m.group(1) + '<script>window.WAIRO=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';</script>' + m.group(2), s, flags=re.S)
    s = re.sub(r'(<!--CONSULT-->).*?(<!--/CONSULT-->)', lambda m: m.group(1) + consult('') + m.group(2), s, flags=re.S)
    idx.write_text(s, encoding='utf-8')
    print(f'{len(COLORS)}色のページと一覧・sitemap（{len(urls)}件）を書き出しました')

if __name__ == '__main__':
    main()
