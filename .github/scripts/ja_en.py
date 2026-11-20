#!/usr/bin/env python3
"""KartBorsa: Japonca kartların ve setlerin İngilizce adları için kaynak verisini toplar.

Kullanım: python3 ja_en.py <veri klasörü>
Kaynaklar: Limitless TCG (Japonca setlerin İngilizce kart listeleri) ve Bulbapedia (eski Japonca setler:
her kart sayfasındaki Japonca ad -> İngilizce ad). Sonuç <veri>/japonca/ja_en.json içine yazılır.
Haftada bir yenilenir (dosya 7 günden yeniyse hiçbir şey yapmaz). Siteye uygulanması: ja_en_uygula.py
"""
import datetime, html, json, os, re, sys, time, urllib.parse, urllib.request

VERI = sys.argv[1]
YOL = f'{VERI}/japonca/ja_en.json'
UA = {'User-Agent': 'KartBorsa/1.0 (kartborsa.com; haftalık ad listesi)'}
BUGUN = datetime.date.today()

eski = {}
try:
    eski = json.load(open(YOL, encoding='utf-8'))
    if (BUGUN - datetime.date.fromisoformat(eski.get('t', '2000-01-01'))).days < 7 and os.environ.get('ZORLA') != '1':
        print('İngilizce ad verisi güncel:', eski.get('t'))
        sys.exit(0)
except SystemExit:
    raise
except Exception:
    pass


def get(url, js=False):
    for t in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                b = r.read().decode('utf-8', 'replace')
                return json.loads(b) if js else b
        except Exception:
            if t == 3:
                raise
            time.sleep(3 * (t + 1))


def temiz(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


# ---------- Limitless ----------
LIM = 'https://limitlesstcg.com'
lim = {}
try:
    sp = get(LIM + '/cards/jp')
    setler = re.findall(r'<a href="/cards/jp/([^"/?]+)"><img[^>]*>\s*([^<]*?)\s*<span class="code annotation">', sp)
    print('Limitless Japonca set:', len(setler), flush=True)
    for kod, ad in setler:
        if kod in lim:
            continue
        try:
            p = get(f'{LIM}/cards/jp/{urllib.parse.quote(kod)}?display=list&translate=en')
        except Exception as e:
            print('  alınamadı', kod, e)
            continue
        m = re.search(r'class="card-set" data-tooltip="([^"]*)"', p)
        kartlar = {}
        for no, _, ad_en in re.findall(
                r'<td><a href="/cards/jp/[^/"]+/([^?"]+)\?translate=en">([^<]*)</a></td>\s*<td><a href="[^"]+">([^<]*)</a>', p):
            kartlar[urllib.parse.unquote(no)] = temiz(ad_en)
        lim[kod] = {'ad': temiz(ad), 'ja': html.unescape(m.group(1)) if m else '', 'k': kartlar}
        time.sleep(0.7)
except Exception as e:
    print('Limitless alınamadı:', e)
    lim = eski.get('lim', {})
print('Limitless: kart listesi olan set', sum(1 for v in lim.values() if v['k']), flush=True)

# ---------- Bulbapedia ----------
API = 'https://bulbapedia.bulbagarden.net/w/api.php'


def bp_html(sayfa):
    r = get(f'{API}?action=parse&page={urllib.parse.quote(sayfa)}&prop=text&format=json&redirects=1', js=True)
    return r['parse']['text']['*'] if 'parse' in r else ''


bp = {'setler': [], 'kart': {}}
try:
    liste = bp_html('List of Japanese Pokémon Trading Card Game expansions')
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', liste, re.S):
        a = re.search(r'href="/wiki/([^"#]+_\(TCG\))"', tr)
        if not a:
            continue
        hucre = [temiz(x) for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
        ja = next((h for h in hucre if re.search(r'[぀-ヿ一-鿿]', h)), '')
        if not ja:
            continue
        baslik = urllib.parse.unquote(a.group(1)).replace('_', ' ')
        yil = re.findall(r'\b(19\d\d|20\d\d)\b', ' '.join(hucre))
        bp['setler'].append([ja, baslik[:-6], int(yil[-1]) if yil else 0])
    print('Bulbapedia Japonca set:', len(bp['setler']), flush=True)
    for ja, baslik, yil in bp['setler']:
        if not yil or yil > 2010 or baslik in bp['kart']:
            continue
        try:
            p = bp_html(baslik + ' (TCG)')
        except Exception as e:
            print('  alınamadı', baslik, e)
            continue
        basliklar = []
        for h in re.findall(r'href="/wiki/([^"#]+)"', p):
            t = urllib.parse.unquote(h).replace('_', ' ')
            if (f'({baslik} ' in t or t.endswith(f'({baslik})')) and t not in basliklar:
                basliklar.append(t)
        m = {}
        for i in range(0, len(basliklar), 50):
            r = get(f'{API}?action=query&prop=revisions&rvprop=content&rvslots=main&format=json&redirects=1&titles='
                    + urllib.parse.quote('|'.join(basliklar[i:i + 50])), js=True)
            for pg in (r.get('query', {}).get('pages') or {}).values():
                t = pg['revisions'][0]['slots']['main']['*'] if pg.get('revisions') else ''
                jm = re.search(r'\|\s*jname\s*=\s*([^\n|]+)', t)
                cm = re.search(r'\|\s*cardname\s*=\s*([^\n|]+)', t)
                if jm and cm:
                    j_ = re.sub(r'\{\{[^}]*\}\}|<[^>]+>', '', jm.group(1)).strip()
                    e_ = re.sub(r'\{\{[^}]*\}\}|<[^>]+>', '', cm.group(1)).strip()
                    if j_ and e_:
                        m.setdefault(j_, [])
                        if e_ not in m[j_]:
                            m[j_].append(e_)
            time.sleep(1)
        bp['kart'][baslik] = m
        time.sleep(1)
except Exception as e:
    print('Bulbapedia alınamadı:', e)
    bp = eski.get('bp', bp)
print('Bulbapedia: kart adı alınan set', sum(1 for v in bp['kart'].values() if v), flush=True)

os.makedirs(f'{VERI}/japonca', exist_ok=True)
json.dump({'t': BUGUN.isoformat(), 'lim': lim, 'bp': bp}, open(YOL, 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('Yazıldı:', YOL, os.path.getsize(YOL) // 1024, 'KB')
