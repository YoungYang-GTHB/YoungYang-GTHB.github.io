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
