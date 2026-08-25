---
name: job-hunter
description: >
  校招智能求职助手。从 offer情报局 增量拉取岗位 → 智能匹配筛选 →
  调用 resume-generator 生成针对性简历 → 辅助浏览器填表投递。
  全程证据驱动，人类在环，不自动投递。
---

# Job Hunter — 校招智能求职助手

## 完整工作流

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│ 1. 岗位获取  │ →  │ 2. 匹配筛选  │ →  │ 3. 简历生成  │ →  │ 4. 辅助投递   │
│ fetch_jobs   │    │ LLM评分      │    │ resume-gen   │    │ form-filler   │
└─────────────┘    └─────────────┘    └─────────────┘    └──────────────┘
```

## 命令速查

```bash
cd skills/job-hunter

# 1. 增量拉取今日新岗位（默认模式）
python3 scripts/fetch_jobs.py

# 2. 查看结果：output/YYYY-MM-DD-jobs.jsonl

# 3. 对选定的岗位生成针对性简历（需 manual 操作 CC）
#    提供 JD 文本，CC 调用 resume-generator 出 PDF

# 4. 生成表单填写用的标准简历 JSON
python3 scripts/profile_mapper.py > /tmp/resume-profile.json

# 5. 浏览器中打开目标投递页面
#    在 Chrome Side Panel 中粘贴 /tmp/resume-profile.json
#    点击「整页填充」

# 6. 查看北京时间当天已到期的官网监测与阶段提醒
#    输出会区分定期检查、预计开放前7日、预计开放日、
#    预计开放后仍未确认、安全日前1日、安全日和已越过安全日。
python3 scripts/jobctl.py monitor-due

# 指定日期预览（只读，不访问招聘站、不提交）
python3 scripts/jobctl.py monitor-due --date 2026-08-18

# 从猎聘“硬科技新主场”专题发现具身/硬科技公司线索。
# 需要已启动的Chrome CDP（默认127.0.0.1:9222）；只输出发现线索，
# 不把猎聘社招/实习职位直接升级为2027校招。
python3 scripts/scan_liepin_hardtech.py

# 如需保存当次快照：
python3 scripts/scan_liepin_hardtech.py \
  --output output/liepin-hardtech-$(date +%F).json

# 一键执行只读日检：同时生成阶段/截止提醒、猎聘快照和运行清单。
# 浏览器不可用时仍保留提醒文件，并在manifest中标记降级。
python3 scripts/run_daily_monitor.py

# 仅生成时间提醒，不访问猎聘：
python3 scripts/run_daily_monitor.py --skip-liepin

# 官网人工/浏览器核验完成后，原子记录证据并排定下一次检查
# 该命令只更新 monitoring.yaml，不进入申请或提交
python3 scripts/jobctl.py monitor-record-check huawei-2027-formal \
  --date 2026-08-18 \
  --evidence '官网仍为2026届应届生；2027普通正式批未开放' \
  --next-check 2026-08-19 \
  --status watching
```

## 架构

```
skills/job-hunter/
├── SKILL.md              # 本文件
├── config.yaml           # 筛选偏好（城市/行业/学历）
├── state.json            # 增量状态（自动管理，gitignored）
├── .token                # API 认证（gitignored）
├── scripts/
│   ├── fetch_jobs.py     # 岗位拉取编排层
│   ├── profile_mapper.py # 个人资料 → form-filler schema
│   ├── auth.py           # Token 生命周期
│   ├── api.py            # REST API 封装
│   ├── state.py          # 增量状态管理
│   ├── run_daily_monitor.py # 只读日检：提醒 + 猎聘快照 + manifest
│   └── tracker.py        # 投递记录追踪
├── records/              # 每日投递记录 CSV
│   └── YYYY-MM-DD.csv
└── references/           # Job OK 评分标准（参考）
```

## 外部工具

| 工具 | 路径 | 用途 |
|------|------|------|
| **form-filler** | `tools/form-filler/` | Chrome 扩展，自动填表 |
| **resume-generator** | `skills/resume-generator/` | LaTeX 简历生成 |

## 使用边界

- 不自动投递，不自动私信 HR
- 不批量爬取招聘平台
- 不编造经历
- 所有外部投递操作需人工确认
- 每次投递前必须先完成该公司当届、当前批次可投岗位的全量检索和横向比较；直达岗位链接、内推链接、历史首选或用户点名岗位都不能跳过本步骤
- 筛岗至少记录岗位总量或检索范围、候选岗位名称/ID/地点、完整 JD、硬性门槛、匹配证据、能力缺口、志愿/次数规则、批次风险和适配度排序；无法取得完整岗位范围或关键规则时，不得进入提交步骤
- 最终岗位必须是当次复核后的最高适配候选，并同时考虑地点偏好、投递额度和在途流程；若选择并非适配度第一的岗位，必须记录明确理由
- 提交前再次确认精确岗位仍在线、岗位 ID 与标题一致、所用简历和内推码正确，并把本次筛岗证据写入监测记录、岗位档案或申请备注；没有可追溯证据的申请不得标记为 `applied`
- 正式秋招监测清单位于 `career/求职投递/2027届/data/monitoring.yaml`；每项必须保留 `submit_gate: user_confirmation`
- `expected_open` 自动产生开放前 T-7/T-1、预计开放日及开放后未确认提醒；`safe_date` 自动产生 T-7/T-3/T-2/T-1、安全日和逾期提醒，不能只依赖 `next_check`；T-2用于兜住在T-3之后才发现的新项目
- 官网公布了精确截止时分时，同时记录带时区的 `hard_deadline_at`（例如 `2026-08-25T02:12:01+08:00`）；其日期必须与 `hard_deadline` 一致。若截止早于 09:00 日报，前一天必须标记“最后可用整日”，不得把截止日白天当作可投时间
- `watching` 与 `tracking` 都必须在预计开放日后持续产生“开放后未确认”提醒；`tracking` 仅表示仍需核验资格或批次关系，不能因此从开放后队列消失
- 提醒输出必须同时显示 `target` 推荐岗位与最终使用的简历；未单独指定时继承清单顶层 `default_resume`，校验会检查简历文件真实存在
- 每个监测项必须记录非空 `official_urls`、`last_checked` 与 `evidence_status`；提醒必须显示最后官网核验日期，动态页面无法读取时不得用页面可访问性代替精确岗位在线证据
- 定期检查、开放节点或安全节点触发时，若 `last_checked` 已距目标日达到 2 天，则附加标记“官网证据已 N 天未更新”；证据陈旧不单独把远期任务提前塞入当日队列，安全日不得凭陈旧证据宣称岗位仍在线
- 当日队列固定按“安全日/已逾期 → 安全日 T-1 → 已开放未筛岗 → 开放预测节点 → 检查逾期 → 定期检查”排序，再在同节点内按 P0/P1/P2 排序，避免 P0 例行检查压住 P1 截止风险
- 人工查看优先使用 `monitor-due --brief`；它会截取常规检查，但所有安全日/已逾期、安全 T-3/T-2/T-1、开放日/T-1 和已开放未筛岗项始终完整显示，并报告未展开的后台巡检数；默认命令仍输出全部到期项
- 每次完成官网核验后优先使用 `monitor-record-check` 同时更新证据和下一检查日；下一检查日必须晚于核验日，避免任务立即重新逾期
- 校验必须阻止时间倒置：`next_check` 必须晚于 `last_checked`，`safe_date` 不得早于 `expected_open`，`open_confirmed_at` 不得晚于 `last_checked`
- 当状态更新为 `open` 时，下次检查最迟为开放后 3 日；若未显式提供更早的官网/内部日期，系统自动把开放后第 7 日设为 `safe_date`。`open` 项不允许缺失安全日
- `open` 项必须记录 `open_confirmed_at`；在完成精确筛岗并转为 `prepared` 前，提醒持续显示“确认开放后 N 日尚未完成筛岗”
