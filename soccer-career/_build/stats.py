#!/usr/bin/env python3
"""Snapshot of finished careers for the topic pages -> data/stats.json.

Reads the live ranking database through wrangler (needs the soccer-career
repo for its wrangler config and a logged-in wrangler):

    python3 soccer-career/_build/stats.py ~/Desktop/soccer-career/server
    python3 soccer-career/_build/build.py && python3 soccer-career/_build/check.py
"""
import datetime, json, pathlib, subprocess, sys

SQL = """SELECT position, COUNT(*) n,
  ROUND(AVG(seasons), 1) seasons, ROUND(AVG(retired_age), 1) age, MAX(retired_age) age_max,
  ROUND(AVG(goals)) goals, MAX(goals) goals_max, ROUND(AVG(assists)) assists, MAX(assists) assists_max,
  ROUND(AVG(clean_sheets)) cs, MAX(clean_sheets) cs_max, ROUND(AVG(apps)) apps
FROM runs WHERE hidden = 0 GROUP BY position"""

def main(server_dir):
    out = subprocess.run(['npx', 'wrangler', 'd1', 'execute', 'soccer-career-ranks', '--remote', '--json',
                          '--command', ' '.join(SQL.split())],
                         cwd=server_dir, capture_output=True, text=True, check=True).stdout
    rows = json.loads(out)[0]['results']
    total = sum(r['n'] for r in rows)
    stats = {'asOf': datetime.date.today().isoformat(), 'all': {'n': total}}
    for r in rows:
        pos = r.pop('position')
        r['share'] = round(100 * r['n'] / total)
        stats[pos] = {k: (int(v) if isinstance(v, float) and v.is_integer() else v) for k, v in r.items()}
    path = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'stats.json'
    path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + '\n')
    print(path, json.dumps(stats['all']))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path.home() / 'Desktop/soccer-career/server'))
