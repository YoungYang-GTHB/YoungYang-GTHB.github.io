# Job Hunter 多 Agent 编排

## 目录

1. 目标与边界
2. 推荐流水线
3. 运行目录
4. 队列操作
5. 并发规则
6. 恢复规则
7. Coordinator 检查单

## 1. 目标与边界

并行处理发现、官网研究、匹配排序和下一家公司预热。保持以下动作串行：

- `applications.yaml`、`monitoring.yaml`、referrals 和 exclusions 的写入；
- 同一 Chrome 用户目录中的表单写操作；
- 登录、验证码、真实性声明和最终提交；
- 成功回执核验及 `record-applied`。

Coordinator 是唯一权威账本写者。Worker 只能读取冻结输入并产生 JSON artifact，
不得直接修改 `career/求职投递/2027届/data/`，不得自动提交或发送申请。

公开 Skill 只保存通用脚本、Schema 和契约。任务运行态默认位于私有子项目：

```text
career/求职投递/2027届/.runtime/job-hunter.sqlite3
```

不要把数据库、WAL、浏览器会话、原始表单快照或含个人信息的 artifact 提交到 Git。

## 2. 推荐流水线

```text
Coordinator
  ├─ Discovery：发现新公司/岗位线索
  ├─ Research A：扫描公司 A 的完整官方岗位池
  ├─ Research B：扫描公司 B 的完整官方岗位池
  └─ Ranking → Form-prep → Audit：复用空闲 worker 槽位

Audit pass
  → Coordinator 运行 jobctl prepare/preflight
  → 用户登录、验证、真实性声明和最终提交
  → Audit 核验官网成功证据
  → Coordinator 运行 record-applied/validate
```

四个并发槽位时保留一个 Coordinator，最多并行两个官网 Research；剩余槽位在
Ranking、Form-prep 和 Audit 之间复用。不要让多个 Worker 同时写共享 Chrome。

## 3. 运行目录

Task 与 artifact 分别遵守：

- `schemas/task.schema.json`
- `schemas/artifact.schema.json`

推荐将不可变产物写入：

```text
career/求职投递/2027届/.runtime/runs/<run_id>/artifacts/
  <task_id>/attempt-<n>.json
```

每次运行冻结并记录输入引用及 SHA-256。能力画像只提供脱敏版本；Discovery、
Research 和 Ranking 不接收身份证、家庭信息、电话号码、Cookie 或登录令牌。
Form-prep 只接收当前字段白名单，并且不能把敏感值写入 artifact。

`input_digest` 固定计算为规范 JSON
`{"input_refs": task.input_refs, "payload": task.payload}` 的 SHA-256。使用
`jobqueue.py dispatch TASK.json` 时会重新读取每个相对 task 文件路径的 input ref 并
校验文件 SHA；输入变化时必须创建新任务版本，不能沿用旧摘要。

## 4. 队列操作

以下示例均不会修改投递账本：

```bash
cd /root/workspace/YoungYang/YoungYang-Resume

# 幂等加入任务
python3 skills/job-hunter/scripts/jobqueue.py dispatch /tmp/research-task.json

# Worker 领取任务；返回完整 task JSON
python3 skills/job-hunter/scripts/jobqueue.py claim \
  --worker research-a --role research --lease-seconds 300

# 长任务定期续租
python3 skills/job-hunter/scripts/jobqueue.py heartbeat TASK_ID \
  --worker research-a --lease-seconds 300

# 先独立校验，再登记完成
python3 skills/job-hunter/scripts/validate_artifact.py \
  /tmp/research-artifact.json --task /tmp/research-task.json
python3 skills/job-hunter/scripts/jobqueue.py complete TASK_ID \
  --worker research-a --artifact /tmp/research-artifact.json

# Coordinator 完成重新审计和单点合并后才标记 consumed
python3 skills/job-hunter/scripts/jobqueue.py consume TASK_ID \
  --coordinator root --artifact-sha256 ARTIFACT_SHA256

# 可重试失败；达到 max_attempts 后自动成为 failed
python3 skills/job-hunter/scripts/jobqueue.py fail TASK_ID \
  --worker research-a --error-code http_503 --message 'official site unavailable' \
  --retry-delay 120

# 需要本人操作时阻断，不自动重试
python3 skills/job-hunter/scripts/jobqueue.py fail TASK_ID \
  --worker form-a --error-code login_required --message '等待本人登录' --blocked

# 需要保留结构化阻断证据时可附加 --artifact blocked-artifact.json

python3 skills/job-hunter/scripts/jobqueue.py status --run-id RUN_ID
```

`dispatch` 对 `idempotency_key` 有唯一约束。相同键、相同语义输入会返回既有任务；
相同键对应不同输入会拒绝。`claim` 在 `BEGIN IMMEDIATE` 事务内领取任务，因此多个
进程不会领取同一项。

## 5. 并发规则

1. Worker 不写权威 YAML、CSV tracker、`state.json` 或生成汇总。
2. Worker 只写自己的唯一 artifact 路径，不共享临时文件。
3. Coordinator 消费 artifact 前必须验证 Schema、`input_digest`、`run_epoch` 和证据时效。
4. 用户改变岗位、地点或简历后增加 `run_epoch`，忽略旧 epoch 的迟到结果。
5. Form-prep 使用 `scripts/browser_lease.py` 获取全局浏览器租约；操作前再次核对
   target ID、域名、公司和岗位 ID，完成或阻断后释放租约。
6. Research 可通过普通联网工具并行；需要共享登录态/CDP 时也必须申请浏览器租约。
7. 最终提交不进入队列自动动作。用户当前交互中的明确确认不能被 Worker 缓存或复用。

建议幂等键组成：

```text
discovery = source + navigation + phase + as_of_date + source_snapshot
research  = company_key + program + phase + as_of_date + official_entry
ranking   = research_sha + profile_sha + preferences_sha + resume_manifest_sha + rubric_version
form_prep = application_key + ranking_sha + field_whitelist_sha + resume_pdf_sha + ats_schema_sha
audit     = form_snapshot_sha + research_sha + current_history_sha + quota_evidence_sha
```

稳定逻辑岗位优先使用官方 job ID；其次使用清除 token、推荐码及追踪参数的官方 URL；
最后才退化为公司、项目、标准化标题和地点。JD 内容哈希是岗位版本，不是逻辑岗位键。
使用 `scripts/canonicalize_job.py` 生成保守的公司键、规范 URL 与逻辑岗位键；品牌名与
法定主体的映射必须来自经核验的 alias 文件，不得靠模糊相似度自动合并。
岗位版本统一调用 `canonicalize_job.job_version()`，对逻辑岗位键、完整 JD、排序后的
地点、在线状态和官网更新时间做规范 JSON 哈希；不要把抓取时间或内推参数混入版本。

## 6. 恢复规则

- Worker 必须在租约过半前 heartbeat。
- 租约过期后，未达到 `max_attempts` 的任务会在下一次 claim 时回到 pending；否则 failed。
- HTTP 429/5xx 使用带延迟的 retry；登录、验证码和声明使用 blocked。
- 重试沿用相同幂等键，每次 attempt 使用新 artifact 路径，禁止覆盖旧证据。
- Worker 崩溃后重新读取网页实际值，不从日志推断表单已保存。
- Coordinator 合并前重新读取权威账本并运行 `jobctl validate`；若输入版本已变化，废弃产物并重跑 Audit。
- `record-applied` 后续视图写入中断时运行 `jobctl reconcile`，不得重复提交官网表单。

## 7. Coordinator 检查单

开始运行：

1. 检查父仓库与 private submodule 工作区。
2. 运行 `jobctl validate` 和 `monitor-due --brief`。
3. 冻结 applications、monitoring、偏好、能力画像和简历 manifest 的哈希。
4. 创建 `run_id`、`run_epoch` 和 task。

消费结果：

1. 验证 artifact 及关联 task。
2. 拒绝旧 epoch、输入哈希不一致和缺少官方证据的 Research。
3. 保留至少前三岗位、完整检索范围、能力缺口、额度与批次风险。
4. 只有 Audit pass 才能创建或更新 prepared 记录。

提交边界：

1. 实时运行 history/preflight，而不是复用 Worker 的旧查询。
2. 向本人展示岗位、地点、简历、内推码、额度和缺口。
3. 等待当前交互明确确认。
4. 本人完成最终提交后核验成功页或候选人中心。
5. `record-applied`、validate、关闭公司标签页，再推进下一家。
