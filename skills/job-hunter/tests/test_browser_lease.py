import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.browser_lease import BrowserLease, BrowserLeaseError


class MutableClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 9, 7, 1, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


class BrowserLeaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temporary.name) / "browser-state"
        self.clock = MutableClock()
        self.manager = BrowserLease(self.state_dir, clock=self.clock)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_acquire_records_owner_and_tight_permissions(self):
        owner = self.manager.acquire(
            agent="agent-a",
            task_id="topstar-53314afc",
            company="拓斯达",
            target_id="target-1",
            origin="https://ehr.tsd.ren/form?access_token=secret#fragment",
            ttl_seconds=60,
        )

        self.assertEqual(owner["agent"], "agent-a")
        self.assertEqual(owner["origin"], "https://ehr.tsd.ren")
        self.assertNotIn("secret", self.manager.owner_path.read_text(encoding="utf-8"))
        self.assertEqual(os.stat(self.state_dir).st_mode & 0o777, 0o700)
        self.assertEqual(os.stat(self.manager.lock_path).st_mode & 0o777, 0o600)
        self.assertEqual(os.stat(self.manager.owner_path).st_mode & 0o777, 0o600)
        self.assertTrue(self.manager.status()["active"])

    def test_second_agent_is_blocked_until_release(self):
        owner = self.manager.acquire(agent="agent-a", task_id="task-a", ttl_seconds=60)

        with self.assertRaisesRegex(BrowserLeaseError, "agent-a / task-a"):
            self.manager.acquire(agent="agent-b", task_id="task-b", ttl_seconds=60)

        self.manager.release(owner["lease_id"])
        next_owner = self.manager.acquire(agent="agent-b", task_id="task-b", ttl_seconds=60)
        self.assertEqual(next_owner["agent"], "agent-b")

    def test_heartbeat_extends_lease_and_can_update_checkpoint(self):
        owner = self.manager.acquire(agent="agent-a", task_id="task-a", ttl_seconds=60)
        original_expiry = owner["expires_at"]
        self.clock.advance(30)

        updated = self.manager.heartbeat(
            owner["lease_id"],
            ttl_seconds=120,
            target_id="target-2",
            mode="human-control",
        )

        self.assertNotEqual(updated["expires_at"], original_expiry)
        self.assertEqual(updated["target_id"], "target-2")
        self.assertEqual(updated["mode"], "human-control")
        self.assertEqual(self.manager.assert_owned(owner["lease_id"])["task_id"], "task-a")

    def test_expired_lease_can_be_replaced_but_not_heartbeated(self):
        owner = self.manager.acquire(agent="agent-a", task_id="task-a", ttl_seconds=10)
        self.clock.advance(11)

        status = self.manager.status()
        self.assertFalse(status["active"])
        self.assertTrue(status["expired"])
        with self.assertRaisesRegex(BrowserLeaseError, "已过期"):
            self.manager.heartbeat(owner["lease_id"], ttl_seconds=60)

        replacement = self.manager.acquire(agent="agent-b", task_id="task-b", ttl_seconds=60)
        self.assertEqual(replacement["agent"], "agent-b")
        self.assertNotEqual(replacement["lease_id"], owner["lease_id"])

    def test_wrong_owner_cannot_heartbeat_or_release(self):
        owner = self.manager.acquire(agent="agent-a", task_id="task-a", ttl_seconds=60)

        with self.assertRaisesRegex(BrowserLeaseError, "不匹配"):
            self.manager.heartbeat("wrong-token", ttl_seconds=60)
        with self.assertRaisesRegex(BrowserLeaseError, "不匹配"):
            self.manager.release("wrong-token")

        self.assertEqual(self.manager.status()["owner"]["lease_id"], owner["lease_id"])

    def test_invalid_origin_and_ttl_are_rejected(self):
        with self.assertRaises(BrowserLeaseError):
            self.manager.acquire(
                agent="agent-a",
                task_id="task-a",
                origin="javascript:alert(1)",
            )
        with self.assertRaises(BrowserLeaseError):
            self.manager.acquire(agent="agent-a", task_id="task-a", ttl_seconds=1)


if __name__ == "__main__":
    unittest.main()
