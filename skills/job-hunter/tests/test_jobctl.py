import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml


SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from scripts.jobctl import (
    ApplicationLedger,
    LedgerError,
    confirmation_token,
    deadline_display,
    enabled_phases,
    ensure_submittable,
    company_category,
    monitor_due_reasons,
    reminder_urgency,
    history_records,
    render_history_table,
    select_brief_rows,
    submission_conflicts,
    resume_guidance,
    render_summary,
    load_monitoring,
    validate_monitor_coverage,
    validate_monitoring,
    write_categorized_summaries,
)


class JobctlTests(unittest.TestCase):
    def make_application(self):
        return {
            "id": "example-robot-role",
            "company": "示例机器人",
            "program": "提前批",
            "position": "Robot Learning 工程师",
            "job_id": "R001",
            "phase": "提前批",
            "policy_status": "current_year_safe",
            "policy_evidence": "当届公告明确不影响正式批",
            "status": "prepared",
            "deadline": "2026-08-30",
            "job_url": "https://jobs.example/R001",
            "locations": ["深圳", "北京"],
            "resume": "public/resume.pdf",
            "channel": "官网投递",
            "referral_code": "",
            "record_verified": False,
            "notes": "",
        }

    def test_confirmation_token_changes_with_material_fields(self):
        application = self.make_application()
        first = confirmation_token(application)
        application["locations"] = ["上海"]
        second = confirmation_token(application)

        self.assertTrue(first.startswith("CONFIRM:example-robot-role:"))
        self.assertNotEqual(first, second)

    def test_deadline_display_preserves_precise_time_and_timezone(self):
        self.assertEqual(
            deadline_display(
                {
                    "hard_deadline": "2026-08-25",
                    "hard_deadline_at": "2026-08-25T02:12:01+08:00",
                }
            ),
            "2026-08-25 02:12+08:00",
        )
        self.assertEqual(deadline_display({"hard_deadline": "2026-08-23"}), "2026-08-23")

    def test_resume_guidance_routes_embodied_infra_and_multimodal_targets(self):
        embodied = resume_guidance({"target": "VLA具身世界模型"})
        infra = resume_guidance({"target": "大模型训练框架与推理系统"})
        multimodal = resume_guidance({"target": "多模态理解算法"})

        self.assertIn("双臂真机", embodied)
        self.assertIn("Triton", infra)
        self.assertIn("数据与评测", multimodal)
        self.assertIn("不虚增", embodied)
        self.assertIn("不虚增", infra)
        self.assertIn("不虚增", multimodal)

    def test_resume_guidance_prefers_explicit_monitor_advice(self):
        advice = "车厂定制建议：突出训练推理优化，不虚增量产智驾经历"
        self.assertEqual(
            resume_guidance({"target": "端到端机器人算法", "resume_advice": advice}),
            advice,
        )

    def test_resume_guidance_uses_evidence_when_target_is_only_an_ats_id(self):
        advice = resume_guidance(
            {
                "target": "J12785",
                "evidence_status": "完整JD覆盖VLA、双臂真机、ROS2与数据评测闭环",
            }
        )

        self.assertIn("双臂真机", advice)
        self.assertIn("不虚增Isaac", advice)

    def test_ledger_round_trip_and_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "applications.yaml"
            summary_path = Path(temp_dir) / "summary.md"
            payload = {
                "schema_version": 1,
                "active_phase": "提前批",
                "updated_at": "2026-08-10",
                "applications": [self.make_application()],
            }
            ledger_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            ledger = ApplicationLedger(ledger_path)
            self.assertEqual(ledger.validate(), [])
            content = render_summary(ledger, summary_path)

            self.assertIn("Robot Learning 工程师", content)
            self.assertIn("待确认", content)
            self.assertTrue(summary_path.exists())

    def test_categorized_summary_splits_company_type_and_lifecycle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            private = self.make_application()
            private.update(status="applied", applied_at="2026-09-03")
            foreign = self.make_application()
            foreign.update(id="foreign-role", company="示例外企", status="held")
            config = {
                "default_category": "私企",
                "category_order": ["央国企及科研院所", "外企", "私企"],
                "overrides": {"示例外企": "外企"},
            }

            stats = write_categorized_summaries(
                [private, foreign], config, Path(temp_dir) / "分类汇总"
            )

            self.assertEqual(company_category("示例机器人", config), "私企")
            self.assertEqual(stats["私企"]["已投递与进行中"], 1)
            self.assertEqual(stats["外企"]["待投递与暂缓"], 1)
            self.assertTrue((Path(temp_dir) / "分类汇总" / "外企" / "README.md").exists())

    def test_submission_gate_enforces_phase_and_policy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "applications.yaml"
            application = self.make_application()
            payload = {
                "schema_version": 1,
                "active_phase": "提前批",
                "updated_at": "2026-08-10",
                "applications": [application],
            }
            ledger_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            ledger = ApplicationLedger(ledger_path)

            ensure_submittable(ledger, application)
            application["phase"] = "秋招"
            with self.assertRaises(LedgerError):
                ensure_submittable(ledger, application)
            application["phase"] = "提前批"
            application["policy_status"] = "unknown"
            with self.assertRaises(LedgerError):
                ensure_submittable(ledger, application)

    def test_submission_gate_allows_parallel_early_and_autumn_phases(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "applications.yaml"
            early = self.make_application()
            autumn = self.make_application()
            autumn.update(id="example-autumn-role", phase="秋招")
            payload = {
                "schema_version": 1,
                "active_phase": "秋招",
                "active_phases": ["提前批", "秋招"],
                "updated_at": "2026-09-03",
                "applications": [early, autumn],
            }
            ledger_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            ledger = ApplicationLedger(ledger_path)
            self.assertEqual(enabled_phases(ledger.data), ["提前批", "秋招"])
            self.assertEqual(ledger.validate(), [])
            ensure_submittable(ledger, early)
            ensure_submittable(ledger, autumn)

    def test_submission_window_blocks_a_second_company_program_application(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "applications.yaml"
            candidate = self.make_application()
            candidate.update(
                id="example-second-role",
                position="具身世界模型部署",
                job_id="R002",
                submission_window={
                    "scope": "company_program",
                    "max_applications": 1,
                    "window_days": 31,
                },
            )
            previous = self.make_application()
            previous.update(
                id="example-first-role",
                position="具身大模型算法",
                job_id="R001",
                status="applied",
                applied_at=date.today().isoformat(),
                submission_window={
                    "scope": "company_program",
                    "max_applications": 1,
                    "window_days": 31,
                },
            )
            payload = {
                "schema_version": 1,
                "active_phase": "提前批",
                "updated_at": date.today().isoformat(),
                "applications": [candidate, previous],
            }
            ledger_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            ledger = ApplicationLedger(ledger_path)

            conflicts = submission_conflicts(ledger, candidate)
            self.assertTrue(any("投递窗口已满" in item for item in conflicts))
            with self.assertRaisesRegex(LedgerError, "投递前去重阻断"):
                ensure_submittable(ledger, candidate)

    def test_history_table_filters_company_and_active_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "applications.yaml"
            active = self.make_application()
            active.update(status="applied", applied_at="2026-08-20")
            held = self.make_application()
            held.update(id="example-held-role", status="held", position="备选岗位")
            payload = {
                "schema_version": 1,
                "active_phase": "提前批",
                "updated_at": "2026-08-20",
                "applications": [active, held],
            }
            ledger_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            records = history_records(
                ApplicationLedger(ledger_path), company="示例机器人", active_only=True
            )

            self.assertEqual([item["id"] for item in records], ["example-robot-role"])
            table = render_history_table(records)
            self.assertIn("| 已投递 | 2026-08-20 | 示例机器人 |", table)

    def test_monitor_due_emits_opening_and_safety_stages(self):
        monitor = {
            "next_check": "2026-08-20",
            "expected_open": "2026-08-25",
            "safe_date": "2026-08-28",
            "last_checked": "2026-08-17",
            "status": "watching",
        }

        self.assertIn(
            "预计开放前7日",
            monitor_due_reasons(monitor, date(2026, 8, 18)),
        )
        self.assertIn(
            "预计开放前1日",
            monitor_due_reasons(monitor, date(2026, 8, 24)),
        )
        self.assertIn(
            "预计开放日",
            monitor_due_reasons(monitor, date(2026, 8, 25)),
        )
        self.assertIn(
            "预计开放后1日未确认",
            monitor_due_reasons(monitor, date(2026, 8, 26)),
        )
        tracking_monitor = {**monitor, "status": "tracking"}
        self.assertIn(
            "预计开放后1日未确认",
            monitor_due_reasons(tracking_monitor, date(2026, 8, 26)),
        )
        prepared_monitor = {**monitor, "status": "prepared"}
        self.assertNotIn(
            "预计开放日",
            monitor_due_reasons(prepared_monitor, date(2026, 8, 25)),
        )
        self.assertFalse(
            any(
                reason.startswith("预计开放后")
                for reason in monitor_due_reasons(prepared_monitor, date(2026, 8, 26))
            )
        )
        self.assertIn(
            "安全日前7日",
            monitor_due_reasons(monitor, date(2026, 8, 21)),
        )
        self.assertIn(
            "安全日前3日",
            monitor_due_reasons(monitor, date(2026, 8, 25)),
        )
        self.assertIn(
            "安全日前2日",
            monitor_due_reasons(monitor, date(2026, 8, 26)),
        )
        self.assertIn(
            "安全日前1日",
            monitor_due_reasons(monitor, date(2026, 8, 27)),
        )
        self.assertIn(
            "安全日",
            monitor_due_reasons(monitor, date(2026, 8, 28)),
        )

    def test_safety_stage_outranks_routine_company_priority(self):
        self.assertLess(
            reminder_urgency(["安全日前1日"]),
            reminder_urgency(["定期检查"]),
        )
        self.assertLess(
            reminder_urgency(["已越过安全日1天"]),
            reminder_urgency(["预计开放日"]),
        )
        self.assertLess(
            reminder_urgency(["安全日前3日"]),
            reminder_urgency(["安全日前7日"]),
        )
        self.assertEqual(
            reminder_urgency(["安全日前2日"]),
            reminder_urgency(["安全日前3日"]),
        )
        self.assertLess(
            reminder_urgency(["预计开放前1日"]),
            reminder_urgency(["预计开放前7日"]),
        )

    def test_brief_compacts_excess_mandatory_rows_without_dropping_them(self):
        mandatory = [
            ({"id": f"urgent-{index}", "company": f"紧急{index}"}, ["安全日"])
            for index in range(4)
        ]
        routine = [
            ({"id": "routine", "company": "常规"}, ["定期检查"])
        ]

        detailed, compact = select_brief_rows(mandatory + routine, 2)

        self.assertEqual([row[0]["id"] for row in detailed], ["urgent-0", "urgent-1"])
        self.assertEqual([row[0]["id"] for row in compact], ["urgent-2", "urgent-3"])
        self.assertEqual(len(detailed) + len(compact), len(mandatory))

    def test_hard_deadline_emits_daily_final_week_reminders_and_outranks_safety(self):
        monitor = {
            "next_check": "2026-08-20",
            "safe_date": "2026-08-20",
            "hard_deadline": "2026-08-23",
            "last_checked": "2026-08-17",
            "status": "prepared",
        }
        reasons = monitor_due_reasons(monitor, date(2026, 8, 17))
        self.assertIn("官方硬截止前6天", reasons)
        self.assertLess(reminder_urgency(reasons), reminder_urgency(["安全日"]))
        self.assertIn(
            "官方硬截止日",
            monitor_due_reasons(monitor, date(2026, 8, 23)),
        )

        monitor["deadline_label"] = "笔试后补投截止"
        custom_reasons = monitor_due_reasons(monitor, date(2026, 8, 19))
        self.assertIn("笔试后补投截止前4天", custom_reasons)
        self.assertLess(reminder_urgency(custom_reasons), reminder_urgency(["安全日"]))

    def test_early_morning_deadline_marks_last_usable_day_before_daily_report(self):
        monitor = {
            "next_check": "2026-08-19",
            "safe_date": "2026-08-19",
            "hard_deadline": "2026-08-25",
            "hard_deadline_at": "2026-08-25T02:12:01+08:00",
            "last_checked": "2026-08-18",
            "status": "prepared",
        }

        previous_day = monitor_due_reasons(monitor, date(2026, 8, 24))
        deadline_day = monitor_due_reasons(monitor, date(2026, 8, 25))

        self.assertIn("最后可用整日（次日02:12截止）", previous_day)
        self.assertIn("官方硬截止已于02:12结束（早于09:00日报）", deadline_day)

    def test_precise_deadline_requires_timezone_and_matching_date(self):
        payload = {
            "default_resume": "public/resume.pdf",
            "monitors": [
                {
                    "id": "bad-precise-deadline",
                    "company": "示例公司",
                    "status": "watching",
                    "priority": "P1",
                    "last_checked": "2026-08-18",
                    "next_check": "2026-08-19",
                    "hard_deadline": "2026-08-25",
                    "hard_deadline_at": "2026-08-24T23:00:00",
                    "evidence_status": "官网公布精确截止时间",
                    "action": "08-19复核官网",
                    "official_urls": ["https://jobs.example.com"],
                    "submit_gate": "user_confirmation",
                }
            ],
        }

        errors = validate_monitoring(payload)
        self.assertTrue(any("必须包含时区偏移" in error for error in errors))
        self.assertTrue(any("日期必须与 hard_deadline 一致" in error for error in errors))

    def test_open_monitor_requires_confirmation_and_safe_dates(self):
        payload = {
            "default_resume": "public/resume.pdf",
            "monitors": [
                {
                    "id": "example-open",
                    "company": "示例公司",
                    "status": "open",
                    "priority": "P0",
                    "next_check": "2026-08-20",
                    "last_checked": "2026-08-17",
                    "evidence_status": "官网已开放",
                    "action": "筛选岗位",
                    "official_urls": ["https://jobs.example.com"],
                    "submit_gate": "user_confirmation",
                }
            ],
        }

        errors = validate_monitoring(payload)
        self.assertTrue(any("safe_date" in error for error in errors))
        self.assertTrue(any("open_confirmed_at" in error for error in errors))

    def test_high_priority_prepared_monitor_requires_safe_date(self):
        payload = {
            "default_resume": "public/resume.pdf",
            "monitors": [
                {
                    "id": "example-prepared",
                    "company": "示例公司",
                    "status": "prepared",
                    "priority": "P0",
                    "next_check": "2026-08-20",
                    "last_checked": "2026-08-17",
                    "evidence_status": "2027正式岗已核验",
                    "action": "在内部安全日前完成决策",
                    "official_urls": ["https://jobs.example.com"],
                    "submit_gate": "user_confirmation",
                }
            ],
        }

        errors = validate_monitoring(payload)
        self.assertTrue(any("P0/P1 prepared" in error for error in errors))
        self.assertTrue(any("target" in error for error in errors))
        self.assertTrue(any("resume" in error for error in errors))

        payload["monitors"][0]["priority"] = "P2"
        self.assertFalse(any("safe_date" in error for error in validate_monitoring(payload)))

    def test_high_priority_prepared_monitor_passes_with_explicit_target_and_resume(self):
        payload = {
            "default_resume": "public/resume.pdf",
            "monitors": [
                {
                    "id": "ready-prepared",
                    "company": "示例公司",
                    "status": "prepared",
                    "priority": "P1",
                    "next_check": "2026-08-20",
                    "last_checked": "2026-08-17",
                    "safe_date": "2026-08-22",
                    "target": "VLA算法工程师",
                    "resume": "public/resume.pdf",
                    "evidence_status": "2027正式岗已核验",
                    "action": "安全日前使用已绑定简历决策",
                    "official_urls": ["https://jobs.example.com"],
                    "submit_gate": "user_confirmation",
                }
            ],
        }

        errors = validate_monitoring(payload)
        self.assertFalse(any("target" in error or "resume" in error for error in errors))

    def test_high_priority_open_monitor_requires_explicit_resume(self):
        payload = {
            "default_resume": "public/resume.pdf",
            "monitors": [
                {
                    "id": "open-needs-resume",
                    "company": "示例公司",
                    "status": "open",
                    "priority": "P1",
                    "next_check": "2026-08-20",
                    "last_checked": "2026-08-17",
                    "open_confirmed_at": "2026-08-17",
                    "safe_date": "2026-08-22",
                    "target": "待补齐精确JD",
                    "evidence_status": "2027项目已开放",
                    "action": "继续筛岗",
                    "official_urls": ["https://jobs.example.com"],
                    "submit_gate": "user_confirmation",
                }
            ],
        }

        errors = validate_monitoring(payload)
        self.assertTrue(any("open/prepared" in error and "resume" in error for error in errors))

    def test_monitor_dates_must_be_chronologically_consistent(self):
        payload = {
            "default_resume": "public/resume.pdf",
            "monitors": [
                {
                    "id": "bad-dates",
                    "company": "示例公司",
                    "status": "watching",
                    "priority": "P1",
                    "last_checked": "2026-08-20",
                    "next_check": "2026-08-20",
                    "expected_open": "2026-08-25",
                    "safe_date": "2026-08-24",
                    "evidence_status": "等待开放",
                    "action": "复核官网",
                    "official_urls": ["https://jobs.example.com"],
                    "submit_gate": "user_confirmation",
                }
            ],
        }

        errors = validate_monitoring(payload)
        self.assertTrue(any("next_check 必须晚于 last_checked" in error for error in errors))
        self.assertTrue(any("safe_date 不能早于 expected_open" in error for error in errors))

    def test_single_action_date_must_match_next_check_but_ranges_are_allowed(self):
        monitor = {
            "id": "dated-action",
            "company": "示例公司",
            "status": "watching",
            "priority": "P1",
            "last_checked": "2026-08-18",
            "next_check": "2026-08-20",
            "evidence_status": "等待开放",
            "action": "08-18复核官网",
            "official_urls": ["https://jobs.example.com"],
            "submit_gate": "user_confirmation",
        }
        payload = {"default_resume": "public/resume.pdf", "monitors": [monitor]}

        errors = validate_monitoring(payload)
        self.assertTrue(any("action 单次起始日期必须与 next_check 一致" in error for error in errors))

        monitor["action"] = "08-18至08-25日检官网"
        self.assertFalse(any("action 单次起始日期" in error for error in validate_monitoring(payload)))

        monitor["action"] = "08-18起每周复核官网"
        self.assertFalse(any("action 单次起始日期" in error for error in validate_monitoring(payload)))

    def test_future_evidence_dates_are_rejected_but_future_reminders_are_allowed(self):
        payload = {
            "updated_at": "2026-08-17T10:00:00+08:00",
            "default_resume": "public/resume.pdf",
            "monitors": [
                {
                    "id": "future-evidence",
                    "company": "示例公司",
                    "status": "watching",
                    "priority": "P1",
                    "last_checked": "2026-08-18",
                    "next_check": "2026-08-19",
                    "expected_open": "2026-09-01",
                    "safe_date": "2026-09-05",
                    "evidence_status": "等待开放",
                    "action": "复核官网",
                    "official_urls": ["https://jobs.example.com"],
                    "submit_gate": "user_confirmation",
                }
            ],
        }

        errors = validate_monitoring(payload)
        self.assertTrue(any("last_checked 不能晚于时间基准" in error for error in errors))
        self.assertFalse(any("expected_open 不能晚于时间基准" in error for error in errors))
        self.assertFalse(any("safe_date 不能晚于时间基准" in error for error in errors))

    def test_application_cannot_be_recorded_after_ledger_time_baseline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "applications.yaml"
            application = self.make_application()
            application.update(status="applied", applied_at="2026-08-18")
            payload = {
                "schema_version": 1,
                "active_phase": "提前批",
                "updated_at": "2026-08-17T10:00:00+08:00",
                "applications": [application],
            }
            ledger_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )

            errors = ApplicationLedger(ledger_path).validate()
            self.assertTrue(any("applied_at 不能晚于时间基准" in error for error in errors))

    def test_duplicate_yaml_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            monitoring_path = Path(temp_dir) / "monitoring.yaml"
            monitoring_path.write_text(
                "default_resume: public/resume.pdf\n"
                "default_resume: public/other.pdf\n"
                "monitors: []\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(LedgerError, "YAML 重复键"):
                load_monitoring(monitoring_path)

    def test_monitor_and_application_hard_deadlines_must_match(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "applications.yaml"
            application = self.make_application()
            application["deadline"] = "2026-08-23"
            payload = {
                "schema_version": 1,
                "active_phase": "提前批",
                "updated_at": "2026-08-17",
                "applications": [application],
            }
            ledger_path.write_text(
                yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            monitoring = {
                "monitors": [
                    {
                        "id": "example-monitor",
                        "hard_deadline": "2026-08-24",
                        "application_ids": [application["id"]],
                    }
                ]
            }

            errors = validate_monitor_coverage(ApplicationLedger(ledger_path), monitoring)
            self.assertTrue(any("官方硬截止不一致" in error for error in errors))

            monitoring["monitors"][0].pop("hard_deadline")
            errors = validate_monitor_coverage(ApplicationLedger(ledger_path), monitoring)
            self.assertTrue(any("缺少 hard_deadline" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
