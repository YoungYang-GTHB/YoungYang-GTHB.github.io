#!/usr/bin/env python3
"""Read-only reminder for worker results requiring coordinator review.

Does not poll live Codex agents, consume artifacts, or send notifications.
"""
import argparse
import json
import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[1] / 'career/求职投递/2027届/.runtime/job-hunter.sqlite3'


def inspect(db):
    if not db.is_file():
        return {'available': False, 'counts': {}}
    with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True) as conn:
        counts = dict(conn.execute('SELECT status, COUNT(*) FROM tasks GROUP BY status'))
    return {'available': True, 'counts': counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=DEFAULT_DB)
    parser.add_argument('--check', action='store_true', help='Return 2 when review/work remains; 3 when unavailable')
    args = parser.parse_args()
    try:
        report = inspect(args.db)
    except sqlite3.Error as exc:
        print(json.dumps({'available': False, 'error': type(exc).__name__}))
        return 3
    print(json.dumps(report, ensure_ascii=False))
    if not report['available']:
        print('Queue unavailable: do not infer that agents are idle or all results handled.')
        return 3 if args.check else 0
    counts = report['counts']
    pending = sum(n for status, n in counts.items() if status != 'consumed')
    if pending:
        print('Coordinator review required: succeeded is not consumed; blocked/failed need an explicit disposition.')
        print('Check live collaboration agents separately. Review evidence and input freshness; never auto-consume to clear this warning.')
        print('Historical/superseded attempts may remain in this queue; counts are not live-agent counts.')
    else:
        print('No queued result remains; still check live agents and tasks not registered in this queue.')
    return 2 if args.check and pending else 0


if __name__ == '__main__':
    raise SystemExit(main())
