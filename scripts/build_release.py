"""Build a map data release from the Google Sheet (exported as .xlsx).

Usage:
  python3 scripts/build_release.py SHEET.xlsx --version "2026 Oct" --released 2026-10-13 \
      [--uc-tab "2026 Oct: Use cases"] [--res-tab "2026 Oct: Resources"] [--notes "..."]

Writes data/releases/<slug>/{use-cases.json, use-cases.csv, resources.csv}
and adds or updates the entry in data/versions.json (newest first).
"""
import argparse, csv, json, os, re, sys
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Sheet step name -> map step key. Old names stay as aliases so older exports still build.
STEP_KEY = {
    'Plan research': 'Planning', 'Prepare research materials': 'Materials', 'Recruit participants': 'Recruiting',
    'Conduct secondary research': 'Desk research', 'Conduct exploratory research': 'Fieldwork',
    'Conduct generative research': 'Fieldwork', 'Conduct evaluative research': 'Evaluation',
    'Prepare data': 'Data prep', 'Code data': 'Coding', 'Analyze quantitatively': 'Quant',
    'Cluster into themes': 'Patterns', 'Model patterns': 'Modelling', 'Frame insights': 'Insights',
    'Build frameworks': 'Frameworks', 'Define design principles and requirements': 'Principles',
    'Generate ideas': 'Ideation', 'Develop concepts': 'Concepts', 'Design interfaces': 'Interface design',
    'Create content and assets': 'Content creation', 'Build functional prototype': 'Functional',
    'Prepare handoff': 'Handoff',
}
TIER_TYPE = {'1': 'Peer-reviewed research', '2': 'Research organizations', '3': 'Preprints',
             '4': 'Practitioners', '5': 'Platforms and tool makers'}
CAT_ORDER = ['General AI assistants', 'Research platforms', 'Design and whiteboard tools',
             'Prototyping and coding tools', 'Image generation', 'Analytics and feedback tools',
             'Meeting and transcription tools', 'Other']


def rows(ws):
    it = ws.iter_rows(values_only=True)
    head = [str(h).strip() if h is not None else '' for h in next(it)]
    out = []
    for r in it:
        if not any(v not in (None, '') for v in r):
            continue
        out.append({h: ('' if v is None else v) for h, v in zip(head, r)})
    return head, out


def s(v):
    return str(v).strip() if v is not None else ''


def bullets(text):
    return [re.sub(r'^[•\-\*]\s*', '', x.strip()) for x in s(text).split('\n') if x.strip()]


def split_desc(d):
    m = re.search(r'(?<=[.!?])\s+(?=[A-Z"\'(])', d)
    return (d[:m.start()], d[m.end():]) if m else (d, '')


def year(v):
    m = re.search(r'(19|20)\d\d', s(v))
    return int(m.group(0)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('xlsx'); ap.add_argument('--version', required=True); ap.add_argument('--released', required=True)
    ap.add_argument('--uc-tab'); ap.add_argument('--res-tab'); ap.add_argument('--notes', default='')
    ap.add_argument('--previous', help='an earlier use-cases.json to carry over source links for unchanged bullets')
    a = ap.parse_args()
    slug = a.version.lower().replace(' ', '-')  # "2026 Oct" -> "2026-oct"
    wb = openpyxl.load_workbook(a.xlsx, read_only=True)
    pick = lambda want, fallbacks: next(t for t in [want] + fallbacks if t and t in wb.sheetnames)
    uc_tab = pick(a.uc_tab, [a.version + ': Use cases', 'Current: Use cases', 'All use cases'])
    res_tab = pick(a.res_tab, [a.version + ': Resources', 'Current: Resources', 'Resources'])
    uc_head, ucs = rows(wb[uc_tab]); res_head, ress = rows(wb[res_tab])
    by_url = {s(r['URL']): r for r in ress if s(r.get('URL'))}

    prev = {}
    if a.previous and os.path.exists(a.previous):
        prev = {u['id']: u for u in json.load(open(a.previous))['useCases']}

    problems, out, tool_cats = [], [], {}
    for r in ucs:
        uid = s(r['ID'])
        step = STEP_KEY.get(s(r['Step']))
        if not uid or not step:
            problems.append(f"Row '{s(r['Use case'])}': missing ID or unknown step '{s(r['Step'])}'"); continue
        res = []
        for i in range(1, 6):
            url = s(r.get(f'Resource {i} URL'))
            if not url:
                continue
            R = by_url.get(url, {})
            if not R:
                problems.append(f'{uid}: resource {i} not in the Resources tab ({url})')
            tier = s(R.get('Authority tier'))[:1]
            res.append({'t': s(r.get(f'Resource {i}')) or s(R.get('Title')), 'u': url,
                        'ty': TIER_TYPE.get(tier, 'Practitioners'), 'y': year(R.get('Publication date')),
                        'a': s(R.get('Author(s)'))})
        old = prev.get(uid, {})

        def linked(text_list, key):
            known = {x['t']: x.get('u') for x in old.get(key, [])}
            items = []
            for t in text_list:
                u = known.get(t)
                if t not in known:  # new bullet: link it to the cited resource named in its brackets
                    cite = (re.findall(r'\(([^()]*)\)\s*$', t) or [''])[0].lower()
                    words = [w for w in re.findall(r"[a-z][a-z/'.&-]{2,}", cite) if w not in ('and', 'the', 'arxiv', 'study', 'report')]
                    for x in res:
                        hay = (x['a'] + ' ' + x['t']).lower()
                        if words and any(w in hay for w in words):
                            u = x['u']; break
                items.append({'t': t, 'u': u or None})
            return items

        tools = [t.strip() for t in s(r['Tools']).split('|') if t.strip()]
        cats = [c.strip() for c in s(r.get('Tool categories')).split('|') if c.strip()]
        for t in tools:
            tool_cats.setdefault(t, set()).update(cats)
        d = s(r['Description']); ds, dr = split_desc(d)
        out.append({
            'id': uid, 'n': s(r['Use case']), 'step': step, 'acc': s(r['Acceptability']).lower(), 'd': d,
            'tools': tools, 'ar': s(r['Acceptability reason']),
            'adv': linked(bullets(r['Advantages']), 'adv'), 'dis': linked(bullets(r['Disadvantages']), 'dis'),
            'pop': s(r['Popularity']).lower(), 'pb': s(r['Popularity basis']),
            'vo': s(r.get('Vendor-only evidence')).lower() == 'yes', 'res': res, 'ds': ds, 'dr': dr,
            'added': s(r['Date added'])[:7], 'rechk': s(r.get('Needs re-check')).lower() == 'yes',
            'verified': s(r.get('Last verified'))[:10],
        })

    # one category per tool: keep the existing assignment, otherwise the category the tool's rows agree on
    known = {}
    cats_file = os.path.join(ROOT, 'data', 'tool-categories.json')
    if os.path.exists(cats_file):
        for c, ts in json.load(open(cats_file)).items():
            for t in ts:
                known[t] = c
    unsure = []
    for t, cs in tool_cats.items():
        cs = {c for c in cs if c in CAT_ORDER}
        if t in known:
            continue
        if t == 'Research prototype':
            known[t] = 'Other'
        elif len(cs) == 1:
            known[t] = next(iter(cs))
        else:
            # pick the category no other tool in those rows already covers
            known[t] = sorted(cs, key=CAT_ORDER.index)[0] if cs else 'Other'; unsure.append((t, sorted(cs)))
    cats = {c: sorted([t for t, k in known.items() if k == c and t in tool_cats], key=str.lower) for c in CAT_ORDER}
    cats = {c: ts for c, ts in cats.items() if ts}
    json.dump({c: sorted([t for t, k in known.items() if k == c], key=str.lower) for c in CAT_ORDER if any(k == c for k in known.values())},
              open(cats_file, 'w'), indent=1, ensure_ascii=False)

    rel_dir = os.path.join(ROOT, 'data', 'releases', slug); os.makedirs(rel_dir, exist_ok=True)
    json.dump({'version': a.version, 'released': a.released, 'toolCategories': cats, 'useCases': out},
              open(os.path.join(rel_dir, 'use-cases.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    for name, head, data in (('use-cases.csv', uc_head, ucs), ('resources.csv', res_head, ress)):
        with open(os.path.join(rel_dir, name), 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=[h for h in head if h], extrasaction='ignore'); w.writeheader(); w.writerows(ucs if name == 'use-cases.csv' else ress)

    vf = os.path.join(ROOT, 'data', 'versions.json')
    vers = json.load(open(vf)) if os.path.exists(vf) else []
    vers = [v for v in vers if v['version'] != a.version]
    vers.append({'version': a.version, 'released': a.released, 'useCases': len(out),
                 'file': f'data/releases/{slug}/use-cases.json', 'notes': a.notes})
    vers.sort(key=lambda v: v['released'], reverse=True)
    json.dump(vers, open(vf, 'w'), indent=1, ensure_ascii=False)

    print(f'{a.version}: {len(out)} use cases, {len(ress)} resources -> data/releases/{slug}/')
    for t, cs in unsure:
        print(f'  tool category guessed: {t} -> {known[t]} (rows say {", ".join(cs)})')
    for p in problems:
        print('  CHECK:', p)


if __name__ == '__main__':
    main()
