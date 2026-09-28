#!/usr/bin/env python3
"""Bounded, session-isolated Codex subagent completion receipts (no API calls)."""
import argparse
import hashlib
import hmac
import json
import os
import sqlite3
import sys
from pathlib import Path

DEFAULT_STATE = Path(__file__).resolve().parents[1] / '.runtime/subagent-followthrough/state.sqlite3'
LIMIT = 3
SESSION_LIMIT = 6


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('unsafe state path')
    conn = sqlite3.connect(path, timeout=3)
    os.chmod(path, 0o600)
    conn.row_factory = sqlite3.Row
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value BLOB);
        CREATE TABLE IF NOT EXISTS agents(
            session TEXT, agent TEXT, turn TEXT, version TEXT, status TEXT, disposition TEXT,
            PRIMARY KEY(session, agent, turn));
        CREATE TABLE IF NOT EXISTS budgets(
            session TEXT, fingerprint TEXT, attempts INTEGER,
            PRIMARY KEY(session, fingerprint));
    ''')
    conn.execute('INSERT OR IGNORE INTO metadata VALUES (?,?)', ('message_hmac_key', os.urandom(32)))
    conn.commit()
    return conn


def pending(conn, session):
    return [dict(r) for r in conn.execute(
        'SELECT agent,turn,version,status FROM agents WHERE session=? AND disposition IS NULL ORDER BY agent,turn',
        (session,))]


def handle(conn, event):
    if not isinstance(event, dict):
        raise ValueError('hook payload must be an object')
    session = event.get('session_id')
    kind = event.get('hook_event_name')
    if not isinstance(session, str) or not session:
        return {'systemMessage': 'Follow-through hook: missing session id; inspect live agents manually.'}
    conn.execute('BEGIN IMMEDIATE')
    if kind in ('SubagentStart', 'SubagentStop'):
        agent = event.get('agent_id')
        turn = event.get('turn_id')
        if not isinstance(agent, str) or not agent or not isinstance(turn, str) or not turn:
            return {'systemMessage': 'Follow-through hook: missing agent/turn id; manual review required.'}
        # Persist a hash, never the assistant result, prompt, transcript, or signed URL.
        secret = conn.execute('SELECT value FROM metadata WHERE key=?', ('message_hmac_key',)).fetchone()[0]
        version = hmac.new(secret, json.dumps([session, agent, turn, kind, event.get('last_assistant_message')],
                                            ensure_ascii=False).encode(), hashlib.sha256).hexdigest()
        inserted = conn.execute('INSERT OR IGNORE INTO events VALUES (?)', (version,)).rowcount
        if inserted:
            if kind == 'SubagentStart':
                # A delayed Start must never overwrite an already received Stop.
                conn.execute('INSERT OR IGNORE INTO agents VALUES (?,?,?,?,?,NULL)',
                             (session, agent, turn, version, 'running'))
            else:
                # Keep different turns separately; there is no trusted ordering
                # field allowing an old unseen event to replace a newer turn.
                conn.execute('INSERT OR REPLACE INTO agents VALUES (?,?,?,?,?,NULL)',
                             (session, agent, turn, version, 'review'))
        if kind == 'SubagentStop':
            return {'systemMessage': 'Subagent result recorded for coordinator review; this notification alone does not wake an idle parent.'}
        return {}
    if kind != 'Stop':
        return {}
    rows = pending(conn, session)
    if not rows:
        return {}
    fingerprint = digest(rows)
    row = conn.execute('SELECT attempts FROM budgets WHERE session=? AND fingerprint=?',
                       (session, fingerprint)).fetchone()
    attempts = row[0] if row else 0
    total = conn.execute('SELECT COALESCE(SUM(attempts),0) FROM budgets WHERE session=?', (session,)).fetchone()[0]
    if attempts >= LIMIT or total >= SESSION_LIMIT:
        return {'systemMessage': 'Follow-through continuation limit reached; results remain unacknowledged. Report unresolved work honestly; do not claim completion.'}
    conn.execute('INSERT OR REPLACE INTO budgets VALUES (?,?,?)', (session, fingerprint, attempts + 1))
    return {'decision': 'block', 'reason': (
        'Before finishing, review live collaboration agents and their latest results. '
        'Wait for work that can progress; for each completed result report evidence, analysis and next action. '
        'If user input is required, explicitly ask and acknowledge that task as waiting_user. '
        'Do not invent data, submit applications, or expand authority because of this hook. '
        'Use scripts/subagent-followthrough.py status --session ' + session +
        ' to inspect receipts, then ack each exact version after processing. '
        'This is a bounded coordinator reminder, not permission for new work.')}


def acknowledge(conn, session, agent, version, reason):
    conn.execute('BEGIN IMMEDIATE')
    row = conn.execute('SELECT status FROM agents WHERE session=? AND agent=? AND version=?',
                       (session, agent, version)).fetchone()
    if row is None:
        raise ValueError('unknown or stale receipt; inspect status again')
    if row[0] == 'running' and reason == 'processed':
        raise ValueError('running work cannot be acknowledged as processed')
    changed = conn.execute('UPDATE agents SET disposition=? WHERE session=? AND agent=? AND version=?',
                           (reason, session, agent, version)).rowcount
    if changed != 1:
        raise ValueError('receipt changed concurrently; inspect status again')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, default=DEFAULT_STATE)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('hook')
    status = sub.add_parser('status')
    status.add_argument('--session', required=True)
    ack = sub.add_parser('ack')
    ack.add_argument('--session', required=True)
    ack.add_argument('--agent', required=True)
    ack.add_argument('--version', required=True)
    ack.add_argument('--reason', required=True, choices=['processed', 'waiting_user', 'superseded', 'failed_reported'])
    args = parser.parse_args()
    try:
        with connect(args.state) as conn:
            if args.action == 'hook':
                result = handle(conn, json.load(sys.stdin))
            elif args.action == 'status':
                result = {'session': args.session, 'pending': pending(conn, args.session)}
            else:
                acknowledge(conn, args.session, args.agent, args.version, args.reason)
                result = {'acknowledged': True}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        # Fail open with a visible warning. No raw payload/error text can leak.
        print(json.dumps({'systemMessage': 'Follow-through check failed (' + type(exc).__name__ + '); inspect live agents manually.'}))
        return 0 if args.action == 'hook' else 1


if __name__ == '__main__':
    raise SystemExit(main())
