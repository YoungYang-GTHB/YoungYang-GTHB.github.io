import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('subagent-followthrough.py')
spec = importlib.util.spec_from_file_location('followthrough', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FollowThroughTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'state.sqlite3'
        self.conn = mod.connect(self.path)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def event(self, kind, session='parent', agent='child', turn='turn1', **extra):
        with self.conn:
            return mod.handle(self.conn, dict(hook_event_name=kind, session_id=session,
                                             agent_id=agent, turn_id=turn, **extra))

    def ack(self, reason='processed'):
        row = mod.pending(self.conn, 'parent')[0]
        with self.conn:
            mod.acknowledge(self.conn, 'parent', row['agent'], row['version'], reason)

    def test_no_work_allows_stop(self):
        self.assertEqual(self.event('Stop'), {})

    def test_running_requires_wait_then_completed_requires_review(self):
        self.event('SubagentStart')
        self.assertEqual(self.event('Stop')['decision'], 'block')
        self.event('SubagentStop')
        self.assertEqual(mod.pending(self.conn, 'parent')[0]['status'], 'review')
        self.ack()
        self.assertEqual(self.event('Stop'), {})

    def test_session_isolation(self):
        self.event('SubagentStop')
        self.assertEqual(self.event('Stop', session='unrelated'), {})

    def test_ack_one_does_not_hide_sibling(self):
        self.event('SubagentStop', agent='a')
        self.event('SubagentStop', agent='b')
        self.ack()
        self.assertEqual([r['agent'] for r in mod.pending(self.conn, 'parent')], ['b'])

    def test_receipts_survive_new_connection(self):
        self.event('SubagentStop')
        other = mod.connect(self.path)
        try:
            self.assertEqual(len(mod.pending(other, 'parent')), 1)
        finally:
            other.close()

    def test_duplicate_does_not_reopen_acknowledged_result(self):
        self.event('SubagentStop', last_assistant_message='done')
        self.ack()
        self.event('SubagentStop', last_assistant_message='done')
        self.assertEqual(self.event('Stop'), {})

    def test_late_duplicate_start_does_not_replace_completion(self):
        self.event('SubagentStart')
        self.event('SubagentStop')
        self.event('SubagentStart')
        self.assertEqual(mod.pending(self.conn, 'parent')[0]['status'], 'review')

    def test_stale_ack_cannot_hide_new_result(self):
        self.event('SubagentStop')
        old = mod.pending(self.conn, 'parent')[0]
        self.event('SubagentStop', last_assistant_message='updated result same turn')
        with self.assertRaises(ValueError):
            mod.acknowledge(self.conn, 'parent', 'child', old['version'], 'processed')

    def test_unseen_old_turn_cannot_hide_new_turn(self):
        self.event('SubagentStart', turn='new')
        self.event('SubagentStop', turn='old')
        rows = mod.pending(self.conn, 'parent')
        self.assertEqual({(r['turn'], r['status']) for r in rows}, {('new', 'running'), ('old', 'review')})

    def test_unseen_start_after_stop_does_not_regress(self):
        self.event('SubagentStop')
        self.event('SubagentStart')
        self.assertEqual(mod.pending(self.conn, 'parent')[0]['status'], 'review')

    def test_session_budget_caps_changing_worksets(self):
        for n in range(mod.SESSION_LIMIT):
            self.event('SubagentStop', turn=str(n))
            self.assertEqual(self.event('Stop')['decision'], 'block')
        self.event('SubagentStop', turn='yet-another')
        self.assertNotIn('decision', self.event('Stop'))

    def test_running_cannot_be_marked_processed(self):
        self.event('SubagentStart')
        with self.assertRaises(ValueError):
            self.ack()

    def test_user_wait_allows_stop_but_new_completion_reopens(self):
        self.event('SubagentStart')
        self.ack('waiting_user')
        self.assertEqual(self.event('Stop'), {})
        self.event('SubagentStop')
        self.assertEqual(self.event('Stop')['decision'], 'block')

    def test_bounded_even_if_continuation_turn_id_changes(self):
        self.event('SubagentStop')
        for n in range(mod.LIMIT):
            self.assertEqual(self.event('Stop', turn=str(n))['decision'], 'block')
        self.assertNotIn('decision', self.event('Stop', turn='new'))
        self.assertTrue(mod.pending(self.conn, 'parent'))

    def test_private_content_not_persisted(self):
        secret = 'test-private-signed-url-and-personal-values'
        self.event('SubagentStop', last_assistant_message=secret, transcript_path=secret)
        self.assertNotIn(secret.encode(), self.path.read_bytes())

    def test_invalid_input_warns_without_blocking(self):
        with self.conn:
            self.assertIn('systemMessage', mod.handle(self.conn, {}))
        result = subprocess.run([sys.executable, str(SCRIPT), '--state', str(self.path), 'hook'],
                                input='invalid json', text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('decision', json.loads(result.stdout))

    def test_non_object_input_fails_open(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--state', str(self.path), 'hook'],
                                input='[]', text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('systemMessage', json.loads(result.stdout))


if __name__ == '__main__':
    unittest.main()
