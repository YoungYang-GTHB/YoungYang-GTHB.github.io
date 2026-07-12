# YoungYang-Resume 项目计划与进度

## 进度总览

| 阶段 | 内容 | 状态 | 产物 |
|------|------|------|------|
| P0 基础架构 | 文件夹骨架 + .gitignore + LaTeX 环境 | ✅ 完成 | 全目录结构 |
| P0 简历模板 v1 | 拉取 LLM-Resume-Template，填入真实数据 | ✅ 完成 | `templates/resume/main.tex` |
| P1 岗位数据集成 | offer情报局 API 封装 + 增量抓取 | ✅ 完成 | `skills/job-hunter/scripts/` |
| P1 自动填表 | Chrome 扩展 + 个人资料映射 | ✅ 完成 | `tools/form-filler/` + `profile_mapper.py` |
| P1 投递追踪 | 每日投递记录 + 统计 | ✅ 完成 | `scripts/tracker.py` + `records/` |
| P1 环境文档 | SETUP.md 完整部署指南 | ✅ 完成 | `SETUP.md` |
| P2 docs/ 文档内容 | 填充所有个人资料 Markdown | 🔜 待填充 | `docs/` 各子目录 |
| P2 resume-generator SKILL | CC Skill 简历自动生成 | 🔜 待编写 | `skills/resume-generator/SKILL.md` |
| P2 网站 /docs 路由 | react-markdown 渲染文档库 | 🔜 待实施 | `src/app/docs/` |
| P2 网站二维码 | qrcode 生成 + LaTeX 集成 | 🔜 待实施 | `public/qr-code.svg` |
| P3 自动求职定时 | Cron 每日 8:00 自动拉取 | 🔜 待配置 | CC CronCreate |
| P3 毕业论文 | NWPU Thesis LaTeX | 2027年 | `templates/thesis/` |

## 核心模块

```
岗位拉取                   投递执行
─────────                ─────────
fetch_jobs.py  ──筛选──→  output/jobs.jsonl
     │                         │
     │  offer情报局 API         │  人工选择
     │  增量拉取                 ↓
     │                    resume-generator  →  output/resumes/*.pdf
     │                         │
     │                         ↓
     │                    form-filler (Chrome扩展)
     │                     一键填充网申表单
     │                         │
     └─────────────────────────┘
                    ↓
              tracker.py → records/YYYY-MM-DD.csv
```

## 参考开源项目

| 模块 | 参考 |
|------|------|
| 文档库 | nanobrain, AI Second Brain |
| 简历模板 | [LLM-Resume-Template](https://github.com/adongwanai/LLM-Resume-Template) |
| 求职 Skill | Job OK, BossHunter, open-resume-agent |
| 自动填表 | [AI-Resume-Form-Filling-Assistant](https://github.com/1lck/AI-Resume-Form-Filling-Assistant) |
| 毕业论文 | [NWPU Thesis LaTeX](https://github.com/NWPUMetaphysicsOffice/Yet-Another-LaTeX-Template-for-NPU-Thesis) |

## 详细计划

→ `/home/gsy/.claude/plans/jaunty-nibbling-canyon.md`
