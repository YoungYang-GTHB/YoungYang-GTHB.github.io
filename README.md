# YoungYang-GTHB.github.io

个人网站、简历生成、岗位检索与自动填表的通用代码仓库。真实个人资料、求职记录和个人化简历源码存放在私有 `career` 子模块中。

基于 Next.js 16 + TypeScript + Tailwind CSS v4 构建。

## 项目结构

```
YoungYang-GTHB.github.io/
├── src/                        # 个人网站源码 (Next.js)
├── examples/                   # 匿名示例数据
├── templates/resume/           # 通用 LaTeX 类与模板基础设施
├── skills/                     # Claude Code Skills
│   ├── resume-generator/       # 简历生成
│   └── job-hunter/             # 岗位拉取 + 投递跟踪
├── tools/form-filler/          # Chrome 扩展：AI 自动填表
├── output/                     # 生成产物（简历 PDF / 岗位 JSONL）
├── career/                     # 私有 YoungYang-Resume 子模块
└── public/                     # 静态资源
```

## 快速启动

```bash
# 安装依赖
npm install
pip install pyyaml requests

# 启动网站
npm run dev        # http://localhost:3000

# 准备真实个人站点（需要私有子模块权限）
./scripts/prepare-private-site.sh
RESUME_DATA_PATH=content/resume.yaml npm run dev

# 编译四份个人简历
./scripts/build-private-resumes.sh
```

## 完整部署指南

→ **[SETUP.md](SETUP.md)** — 环境安装、插件配置、账号准备、故障排查

## 文档

| 文档 | 说明 |
|------|------|
| [SETUP.md](SETUP.md) | 环境部署与配置指南 |
| [PLAN.md](PLAN.md) | 项目计划与进度 |
| [skills/job-hunter/SKILL.md](skills/job-hunter/SKILL.md) | 求职工具使用说明 |

## 环境要求

- Node.js ≥20.9.0
- Python ≥3.9
- TeX Live ≥2021（XeLaTeX）
- Chrome/Edge 浏览器

## 许可证

- 项目代码：MIT
- LaTeX 简历模板：CC BY 4.0（基于 [LLM-Resume-Template](https://github.com/adongwanai/LLM-Resume-Template)）
