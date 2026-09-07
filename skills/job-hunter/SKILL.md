---
name: job-hunter
description: >
  证据驱动、人类在环的校招求职助手。用于增量发现岗位、核验公司完整官方岗位池、
  对照真实经历筛选排序、准备简历和招聘表单、投递前去重审计、提交后落账与招聘监测；
  支持用 Coordinator 调度 discovery/research/ranking/form-prep/audit Worker 并行预研，
  但不自动登录、处理验证码、同意真实性声明或最终提交。
---

# Job Hunter

## 启动检查

在仓库根目录依次执行：

```bash
git submodule update --init --recursive
./scripts/agent-status.sh
python3 skills/job-hunter/scripts/jobctl.py validate
python3 skills/job-hunter/scripts/jobctl.py monitor-due --brief
```

完整阅读：

1. `AGENTS.md`；
2. `career/AGENT_HANDOFF.md`；
3. `career/求职投递/2027届/投递执行规范.md`；
4. `career/求职投递/个人信息字段库.md` 和地点/岗位偏好；
5. 操作公司的 applications、monitoring、官网个人中心和投递记录。

私有子模块不可用时，停止个性化填表和投递状态写入。

## 单公司流程

```text
线索发现
→ 当届官方证据核验
→ 当前批次完整岗位池扫描
→ 历史投递、额度和批次冲突检查
→ 至少前三岗位证据化排序
→ jobctl prepare/preflight
→ 普通表单准备
→ 本人处理登录、验证码、声明和身份字段
→ 当前交互明确确认最终提交
→ 本人完成最终提交
→ 官网成功页/个人中心核验
→ record-applied + validate + 关闭公司标签页
```

`go`、`继续` 或点名公司只授权检索、排序和准备，不是最终提交确认。未完成完整
岗位池、精确 JD、岗位 ID、地点、志愿规则或批次风险核验时保持 watching/held，
不得为了提速推断可投。

始终使用真实经历。实习单位固定写作 **IDEA研究院：视启未来**，岗位写作
**VLA与世界模型实习生**。部署优化不能包装成大规模训练负责人；不得虚增强化学习
项目、双足控制、CUDA Kernel、量化训练、量产自动驾驶、顶会论文等经历。

匹配、截止和额度风险相当时，地点顺序为：苏州、杭州、其他非北京、北京。当前只
推进账本中 `active_phases` 允许的批次；不以第三方线索替代官网证据。

## 多 Agent 编排

当任务涉及多家公司、岗位池较大或需要在当前表单等待期间预热后续公司时，使用
Coordinator + Worker 流水线。开始前完整阅读：

- `references/orchestration.md`：队列、租约、幂等、并发与恢复；
- `references/worker-contracts.md`：各 Worker 输入输出和禁止动作；
- `references/private-profile.md`：私有表单字段、附件白名单和最小披露；
- `schemas/task.schema.json` 与 `schemas/artifact.schema.json`。

核心边界：

- Coordinator 是 applications、monitoring、referrals、exclusions 的唯一写者；
- Worker 只读冻结输入并写独立 artifact；
- 共享 Chrome 的表单写操作一次只允许一个 Form-prep Worker；
- 队列成功仅代表产物有效，不代表已经投递；
- 最终提交、登录、验证码和真实性声明始终由本人完成。

运行态队列默认位于私有且不应提交的：

```text
career/求职投递/2027届/.runtime/job-hunter.sqlite3
```

常用命令：

```bash
python3 skills/job-hunter/scripts/jobqueue.py dispatch TASK.json
python3 skills/job-hunter/scripts/jobqueue.py claim --worker research-a --role research
python3 skills/job-hunter/scripts/jobqueue.py heartbeat TASK_ID --worker research-a
python3 skills/job-hunter/scripts/validate_artifact.py ARTIFACT.json --task TASK.json
python3 skills/job-hunter/scripts/jobqueue.py complete TASK_ID --worker research-a --artifact ARTIFACT.json
# form_prep 还必须追加：--browser-lease-id "$BROWSER_LEASE_ID"
python3 skills/job-hunter/scripts/jobqueue.py consume TASK_ID --coordinator root --artifact-sha256 SHA256
python3 skills/job-hunter/scripts/jobqueue.py status --run-id RUN_ID
python3 skills/job-hunter/scripts/browser_lease.py status
python3 skills/job-hunter/scripts/canonicalize_job.py --company "公司名" --job-id JOB_ID
```

## 岗位发现与监测

Offer 情报局只用于发现和初筛：

```bash
python3 skills/job-hunter/scripts/fetch_jobs.py --wechat-login
python3 skills/job-hunter/scripts/jobctl.py scan --phase 秋招
python3 skills/job-hunter/scripts/jobctl.py shortlist --phase 秋招
python3 skills/job-hunter/scripts/run_daily_monitor.py
python3 skills/job-hunter/scripts/jobctl.py monitor-due --kind apply --brief
python3 skills/job-hunter/scripts/jobctl.py monitor-due --kind process --brief
```

猎聘硬科技专题同样只产生线索：

```bash
python3 skills/job-hunter/scripts/scan_liepin_hardtech.py
```

每条可投结论必须回到公司官方招聘站或官方职位接口核验届别、全职、精确 JD、
地点、截止、志愿上限、在线状态和批次影响。

## 投递门禁与落账

提交前至少运行：

```bash
python3 skills/job-hunter/scripts/jobctl.py history --company "公司名"
python3 skills/job-hunter/scripts/jobctl.py preflight APPLICATION_ID
```

`applications.yaml` 是唯一投递事实源。只有官网成功回执或个人中心精确记录验证后才
执行 `record-applied`；随后运行 `validate`。Markdown 汇总和 CSV tracker 是派生视图，
失败时使用 `reconcile` 恢复，不能据此重复提交官网表单。

Worker 与运行日志不得保存密码、Cookie、验证码、access token、身份证号或带敏感
查询参数的 URL。普通字段可通过 CDP 辅助填写，但最终提交前必须向本人汇报岗位、
地点、简历、内推码、志愿占用、主要能力缺口和未决表单字段。
