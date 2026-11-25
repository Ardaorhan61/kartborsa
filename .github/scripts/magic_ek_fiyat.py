"""Restore prices for exact paper printings linked by Scryfall ID to MTGJSON UUID."""

import gzip
import json
import math
import sys
import urllib.request
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


PROVIDERS = {
    'cm': ('cardmarket', 'Cardmarket', 'EUR'),
    'tp': ('tcgplayer', 'TCGplayer', 'USD'),
    'mp': ('manapool', 'Mana Pool', 'USD'),
    'ck': ('cardkingdom', 'Card Kingdom (mağaza satış fiyatı)', 'USD'),
}


def fresh(day, today):
    try:
        return today - timedelta(days=7) <= date.fromisoformat(day) <= today
    except (TypeError, ValueError):
        return False


def valid(value):
    return type(value) in (float, int) and math.isfinite(value) and value > 0


def daily_quotes():
    req = urllib.request.Request('https://mtgjson.com/api/v5/AllPricesToday.json.gz',
                                 headers={'User-Agent': 'KartBorsa/1.0 (+https://www.kartborsa.com)'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response, gzip.GzipFile(fileobj=response) as stream:
            return json.load(stream)
    except (OSError, ValueError, EOFError) as exc:
        print(f'MTGJSON günlük dosyası alınamadı, yakın tarihli doğrulanmış kayıtlar kullanılacak: {exc}')
        return {}


def quote(row, dates, daily, today):
    provider, finish, value, day_idx, uid = row
    code, label, currency = PROVIDERS[provider]
    day = dates[day_idx]
    published_day = (daily.get('meta') or {}).get('date')
    if uid and fresh(published_day, today):
        card = ((daily.get('data') or {}).get(uid) or {}).get('paper') or {}
        prices = card.get(code) or {}
        new_value = ((prices.get('retail') or {}).get(finish) or {}).get(published_day)
        if prices.get('currency') == currency and valid(new_value):
            value, day = new_value, published_day
    if valid(value) and fresh(day, today):
        return {'k': label, 'para': currency, 'f': finish, 't': value, 'g': day, 'veri': 'MTGJSON' if uid else 'Cardmarket'}
    return None


def run(site, seed, daily, today):
    catalog_path = site / 'cards_mg.json'
    summary_path = site / 'fiyat' / 'ozet_mg.json'
    if not catalog_path.is_file() or not summary_path.is_file():
        return Counter()
    catalog = json.loads(catalog_path.read_bytes())
    summary = json.loads(summary_path.read_bytes())
    set_quotes = {}
    counts = Counter()
    for card in catalog['cards']:
        cid = card[14]
        row = seed['cards'].get(cid)
        old = summary['c'].get(cid) or []
        if not row or any(map(valid, old[:4] + old[7:8])):
            continue
        found = quote(row, seed['dates'], daily, today)
        if not found:
            continue
        sid = catalog['sets'][card[1]][0]
        set_quotes.setdefault(sid, {})[cid] = found
        usd = found['t'] if found['para'] == 'USD' else None
        eur = found['t'] if found['para'] == 'EUR' else None
        summary['c'][cid] = [usd, eur, None, None, None, None, None, None, found['k']]
        counts[found['k']] += 1
    for sid, quotes in set_quotes.items():
        path = site / 'fiyat' / 'set' / f'{sid}.json'
        entries = json.loads(path.read_bytes()) if path.is_file() else {'c': {}}
        for cid, found in quotes.items():
            entries['c'].setdefault(cid, {})['ek_mg'] = found
        path.write_text(json.dumps(entries, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    if counts:
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return counts


if __name__ == '__main__':
    today = datetime.now(timezone(timedelta(hours=3))).date()
    seed = json.loads(Path(sys.argv[2]).read_bytes())
    print('Doğrulanmış Magic fiyatları:', dict(run(Path(sys.argv[1]), seed, daily_quotes(), today)))

