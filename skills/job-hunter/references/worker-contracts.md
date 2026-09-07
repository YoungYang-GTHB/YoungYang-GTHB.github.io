# Job Hunter Worker 契约

## 目录

1. 通用契约
2. Discovery
3. Research
4. Ranking
5. Form-prep
6. Audit
7. Coordinator 消费规则

## 1. 通用契约

每个 Worker 只处理一个有界 task。开始前检查：

- `schema_version`、`run_id`、`run_epoch`、`task_id` 和 role；
- 输入文件 SHA-256 与 `input_digest`；
- 任务没有过期或被取消；
- 输入不含密码、Cookie、验证码、身份证号或招聘站 access token。

执行中定期 heartbeat。只产生一个符合 `artifact.schema.json` 的最终产物；过程日志
不得作为事实源。官网事实与推断分开记录，每条重要结论附 evidence。URL 必须去除
token、peopleId、candidateId 等敏感查询参数。

Worker 永远不得：

- 修改 applications、monitoring、referrals、exclusions 或 recruiting process；
- 调用 `jobctl prepare`、`record-applied` 或修改投递状态；
- 编造候选人经验；
- 自动执行最终提交、发送邮件、同意真实性声明或处理验证码。

## 2. Discovery

### 输入 payload

```json
{
  "sources": [{"source_id": "offer-autumn", "url": "..."}],
  "active_phases": ["提前批", "秋招"],
  "as_of": "2026-09-07",
  "target_keywords": ["VLA", "世界模型", "机器人系统", "嵌入式"],
  "known_company_keys": [],
  "excluded_job_keys": []
}
```

### 输出 facts

```json
{
  "leads": [
    {
      "company": "公司名称",
      "company_key_candidate": "canonical-key-candidate",
      "title": "线索标题",
      "phase_hint": "秋招",
      "source_url": "...",
      "observed_at": "...",
      "evidence_level": "discovery_only",
      "requires_official_verification": true
    }
  ],
  "coverage": {"sources": 1, "records_scanned": 0}
}
```

第三方线索不得输出 `open=true` 或 `eligible=true`。发现页可访问不等于精确岗位在线。

## 3. Research

### 输入 payload

```json
{
  "company_key": "company-key",
  "official_entries": ["https://..."],
  "active_phases": ["提前批", "秋招"],
  "as_of": "2026-09-07",
  "required_tracks": ["具身/VLA", "部署优化", "机器人系统", "嵌入式"],
  "history_snapshot_ref": {"path": "...", "sha256": "..."}
}
```

### 输出 facts

```json
{
  "pool_scan": {
    "official_entry": "https://...",
    "scanned_at": "...",
    "total_jobs": 0,
    "pages_or_query_scope": "all pages",
    "complete": true,
    "graduation_year_verified": true,
    "full_time_verified": true
  },
  "jobs": [
    {
      "job_key": "...",
      "job_version": "...",
      "official_job_id": "...",
      "title": "...",
      "locations": [],
      "phase": "秋招",
      "employment_type": "全职",
      "published_at": "",
      "status": "online",
      "jd": {"duties": [], "requirements": [], "nice_to_have": []},
      "official_url": "..."
    }
  ],
  "application_rules": {
    "max_applications": null,
    "window_days": null,
    "can_modify": null,
    "phase_interaction": "unknown",
    "deadline": ""
  },
  "unknowns": []
}
```

成功 Research 至少包含一条官方 evidence。岗位池、届别、完整 JD 或精确岗位状态
无法验证时返回 blocked，不用搜索摘要或第三方材料补成“已确认”。Research 不排名。
`pool_scan.total_jobs` 必须与输出 `jobs` 数量一致；完整扫描到零岗时二者都写 0，不能
用空数组配合非零计数声称扫描完成。

`job_version` 使用 `canonicalize_job.job_version()` 生成：对 `job_key`、完整 `jd`、
排序后的地点、岗位状态和官网 `updated_at` 做规范 JSON 序列化后计算 SHA-256。任一
实质字段变化都会触发新的版本和后续重新排名；不得使用抓取时间或推荐参数生成版本。

## 4. Ranking

### 输入 payload

```json
{
  "research_artifact_ref": {"path": "...", "sha256": "..."},
  "capability_profile_ref": {"path": "...", "sha256": "..."},
  "preferences_ref": {"path": "...", "sha256": "..."},
  "resume_manifest_ref": {"path": "...", "sha256": "..."},
  "rubric_version": "1"
}
```

### 输出 facts

```json
{
  "ranking": [
    {
      "rank": 1,
      "job_key": "...",
      "hard_gate": "pass",
      "overall_score": 0,
      "scores": {
        "experience_fit": 0,
        "deployment_fit": 0,
        "research_fit": 0,
        "location_fit": 0,
        "quota_risk": 0,
        "phase_risk": 0,
        "evidence_quality": 0
      },
      "matching_evidence": [],
      "capability_gaps": [],
      "exclusion_reason": ""
    }
  ],
  "recommendation": {
    "job_key": "...",
    "resume": "public/resume-vla-zh.pdf",
    "reason": "...",
    "non_top_fit_override_reason": ""
  }
}
```

必须列出前三；不足三岗时列出全部。硬门槛失败不能靠软分数成为推荐项。地点仅在
岗位匹配、截止和额度风险相当时应用“苏州 > 杭州 > 其他非北京 > 北京”。不得将
JD 要求改写成已有经验；明确保留能力缺口。

`hard_gate` 只允许 `pass`、`conditional`、`fail`。各 score 均为 0–100：fit 与
`evidence_quality` 越高越好，`quota_risk`、`phase_risk` 越高风险越大。Worker 必须在
artifact 中说明 `overall_score` 的权重；无论总分多高，都不能推荐 `hard_gate=fail`
的岗位。推荐 `conditional` 岗位时必须写清提交前还需核验的条件。

## 5. Form-prep

### 输入 payload

```json
{
  "selected_job_ref": {"path": "...", "sha256": "..."},
  "browser_target_id": "...",
  "allowed_field_names": ["姓名", "学校", "专业"],
  "resume": {"path": "...", "sha256": "..."},
  "ats_schema_ref": {"path": "...", "sha256": "..."}
}
```

### 输出 facts

```json
{
  "form_snapshot": {
    "company_key": "...",
    "job_id": "...",
    "title": "...",
    "page_url": "已清除敏感参数的URL",
    "filled_fields": ["姓名", "学校", "专业"],
    "validation_errors": []
  },
  "missing_fields": [],
  "resume": {"filename": "resume-vla-zh.pdf", "sha256": "..."}
}
```

Form-prep 必须持有共享 Chrome 的独占租约。artifact 只记录字段名称、存在性和非敏感
选择，不记录身份证号、电话号码、家庭信息值或登录数据。它可以保存普通草稿，不能
点击最终提交。登录、验证码、声明仍返回 `blocked_user_action`；身份字段先检查本人
已有的明确授权，已授权从私有字段库填写的项目可按需读取并填写，不重复要求手填。
任务只传来源路径、哈希和字段名，不内嵌敏感值。

### 填表完成与升级标准

1. 最小字段画像缺项时，先查任务显式给出的权威字段库、结构化资料对应段及附件索引。
   未映射、未查找、资料冲突、真正缺失、控件失败是不同状态，不得统称“资料没有”。
2. 紧急联系人按本人指定关系和库内确值填写；不得由此推断公司内亲属、利益冲突等答案。
   城市从当前岗位允许地点中按既定偏好选择；全局意向字段才使用全局城市优先级。
   到岗时间沿用已授权的毕业后时间；最低接受薪资不自行改写为精确期望薪资。
3. 附件核验学校、学段、文件类型、用途和存在性；索引未收录时继续查权威库引用，
   不直接要求用户重复提供。证件附件与普通简历分别受用途约束，不能互相替代。
4. 简历解析结束后重查教育行数量、真实专业、实习单位/岗位及日期。下拉框检查选中
   标签或可访问状态，不仅看隐藏 input.value；级联/多选用真实交互，重渲染后重新定位。
5. 优先完成所有可填字段。有限重试后仍失败的控件上报 `control_error`，由 Coordinator
   复核或接手，不能直接把技术失败转成用户缺资料。保存成功还须回读关键字段和附件。
6. 只汇总仍未解决的字段，按 `source_missing`、`source_conflict`、`document_mismatch`、
   `control_error`、`user_action_required` 分类，记录已查来源、字段名、是否必填和错误摘要，
   不记录敏感值。先向 Coordinator 报告，不直接向用户索要已有资料。
7. 暂存不是提交。最终提交前提供岗位/ID、地点、简历版本、额度、表单核验和剩余事项；
   仅最终提交授权仍缺失时才请求该确认，不重新询问已获授权的填写动作。

完成任务时还必须把当前租约传给队列：

```bash
python3 scripts/jobqueue.py complete TASK_ID --worker WORKER \
  --artifact ARTIFACT.json --browser-lease-id "$BROWSER_LEASE_ID"
```

队列会再次断言租约的 `agent`、`task_id` 与 `browser_target_id`；租约过期、换页或
由其他 Worker 持有时拒绝接收产物。租约 ID 只用于即时校验，不写入任务或 artifact。

## 6. Audit

### 输入 payload

```json
{
  "research_ref": {"path": "...", "sha256": "..."},
  "ranking_ref": {"path": "...", "sha256": "..."},
  "form_snapshot_ref": {"path": "...", "sha256": "..."},
  "current_history_ref": {"path": "...", "sha256": "..."},
  "evidence_max_age_hours": 24,
  "stage": "pre_submit"
}
```

### 输出 facts

```json
{
  "decision": "pass",
  "checks": [
    {"name": "official_job_online", "result": "pass", "detail": "..."},
    {"name": "history_and_quota", "result": "pass", "detail": "..."},
    {"name": "resume_and_form", "result": "pass", "detail": "..."}
  ]
}
```

允许的 decision：`pass`、`blocked`、`needs_user_action`。Pre-submit Audit 必须检查：

- 精确岗位在线、ID/标题/地点一致；
- Research 证据未过期；
- 已完成公司完整岗位池和前三排序；
- 最新本地账本与官网个人中心均无重复；
- 志愿数、窗口、批次风险和内推码；
- 简历 SHA、表单校验和未决字段。

Post-submit Audit 只接受官网成功页、候选人中心精确岗位或官方邮件。表单保存、按钮
点击、用户口头说“已填写”都不是提交成功证据。

## 7. Coordinator 消费规则

Coordinator 消费 artifact 时必须：

1. 运行 `validate_artifact.py --task`；
2. 校验 artifact 的文件 SHA 与队列记录；
3. 校验当前 `run_epoch` 和输入引用；
4. 重新读取权威账本，不信任任务创建时的历史快照；
5. Audit pass 后才运行 `jobctl prepare/preflight`；
6. 当前交互取得本人确认后才进入最终提交；
7. 成功证据核验后才运行 `record-applied`。

队列中的 `succeeded` 只表示 Worker 产物有效，不表示岗位已经投递。
