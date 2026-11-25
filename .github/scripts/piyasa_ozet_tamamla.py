"""Restore omitted catalogue prices from the same printing's recent source record."""

import json
import math
import sys
from datetime import date, timedelta, timezone, datetime
from pathlib import Path


def positive(value):
    return value if type(value) in (int, float) and math.isfinite(value) and value > 0 else None


def latest_date(value):
    try:
        return date.fromisoformat(value.replace('/', '-'))
    except (ValueError, AttributeError):
        return None


def fresh(value, today):
    day = latest_date(value)
    return day is not None and today - timedelta(days=7) <= day <= today


def market_values(entry, today):
    history = sorted((row for row in entry.get('h', []) if len(row) >= 3 and fresh(row[0], today)), key=lambda row: row[0])
    usd = eur = avg7 = avg30 = avg_sell = None
    if fresh(entry.get('tu'), today):
        variants = entry.get('t') or {}
        primary = variants.get(entry.get('v'))
        if isinstance(primary, list) and len(primary) >= 4:
            usd = positive(primary[3])
    if fresh(entry.get('mu'), today):
        market = (entry.get('m') or []) + [None] * 6
        avg_sell, eur, avg7, avg30 = map(positive, (market[0], market[2], market[4], market[5]))
    if history:
        _, last_usd, last_eur = history[-1][:3]
        usd = usd or positive(last_usd)
        eur = eur or positive(last_eur)
    if not (usd or eur or avg7 or avg30 or avg_sell):
        return None
    previous = history[-2] if len(history) >= 2 else (None, None, None)
    values = [usd, eur, avg7, avg30, positive(previous[1]), positive(previous[2]), previous[0]]
    return values if any(values[:4]) else [*values, avg_sell]


def restore(root, today):
    prices = root / 'fiyat'
    changed = {}
    for summary_name, catalog_names in (
        ('ozet.json', ('cards.json', 'cards_ja.json', 'cards_cp.json')),
        ('ozet_mg.json', ('cards_mg.json',)),
    ):
        path = prices / summary_name
        if not path.is_file():
            continue
        summary = json.loads(path.read_bytes())
        restored = 0
        for name in catalog_names:
            catalog_path = root / name
            if not catalog_path.is_file():
                continue
            catalog = json.loads(catalog_path.read_bytes())
            missing = {}
            for card in catalog['cards']:
                cid = card[14]
                values = summary['c'].get(cid) or []
                if any(map(positive, values[:4])) or len(values) > 7 and positive(values[7]):
                    continue
                sid = catalog['sets'][card[1]][0]
                missing.setdefault(sid, []).append(cid)
            for sid, ids in missing.items():
                set_path = prices / 'set' / f'{sid}.json'
                if not set_path.is_file():
                    continue
                entries = json.loads(set_path.read_bytes()).get('c', {})
                for cid in ids:
                    values = market_values(entries.get(cid) or {}, today)
                    if values:
                        summary['c'][cid] = values
                        restored += 1
        if restored:
            temp = path.with_suffix('.tmp')
            temp.write_text(json.dumps(summary, separators=(',', ':'), ensure_ascii=False), encoding='utf-8')
            temp.replace(path)
        changed[summary_name] = restored
    return changed


if __name__ == '__main__':
    today = datetime.now(timezone(timedelta(hours=3))).date()
    for name, count in restore(Path(sys.argv[1]), today).items():
        print(f'{name}: {count} fiyat tamamlandi')

