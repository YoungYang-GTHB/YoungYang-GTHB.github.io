import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name('agent-results-check.py')


class ResultCheckTest(unittest.TestCase):
    def run_check(self, states=None):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'queue.sqlite3'
            if states is not None:
                with sqlite3.connect(db) as conn:
                    conn.execute('CREATE TABLE tasks(status TEXT)')
                    conn.executemany('INSERT INTO tasks VALUES (?)', [(s,) for s in states])
                before = db.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT), '--db', str(db), '--check'], capture_output=True, text=True)
            if states is not None:
                self.assertEqual(before, db.read_bytes())
            else:
                self.assertFalse(db.exists())
            return result

    def test_missing_is_unknown_not_success(self):
        self.assertEqual(self.run_check().returncode, 3)

    def test_consumed_is_clear(self):
        self.assertEqual(self.run_check(['consumed']).returncode, 0)

    def test_every_unhandled_state_warns(self):
        for state in ['succeeded', 'blocked', 'failed', 'running', 'pending']:
            with self.subTest(state=state):
                self.assertEqual(self.run_check([state]).returncode, 2)


if __name__ == '__main__':
    unittest.main()
