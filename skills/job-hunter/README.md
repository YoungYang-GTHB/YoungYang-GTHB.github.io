# Job OK

[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-job--ok-blue)](#quick-start)
[![For Chinese Job Seekers](https://img.shields.io/badge/中文求职者-优先-black)](#why-job-ok)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

面向中文求职者的证据驱动求职 Agent Skill：**不编经历，不自动海投，只把真实经历变成可投递、可面试、可复盘的求职证据系统。**

## Why Job OK

很多求职者的问题不是“完全没有能力”，而是：

- 简历只会写“参与、协助、负责”，没有动作和结果；
- 面试一追问项目细节就散；
- JD 看了很多，但不知道自己该投什么；
- 用 AI 改简历时，很容易从“表达优化”滑向“包装和编造”。

Job OK 的思路是把求职拆成一个本地工作流：

```text
真实经历
  ↓
证据链
  ↓
岗位信号
  ↓
真实 JD 匹配
  ↓
简历版本
  ↓
面试故事库
  ↓
投递跟踪与复盘
```

它不是求职捷径，而是一套逼你把自己讲清楚的系统。

## Features

| 模块 | 产物 | 解决的问题 |
|---|---|---|
| Intake | `profile.yaml` | 先问清目标城市、岗位、约束和风险，不急着改简历 |
| 经历资产库 | `experience-assets.md` | 把项目、实习、社团、自学、兼职整理成真实材料 |
| 优势挖掘 | `strengths.md` | 每个优势必须走完 `证据 -> 行为 -> 能力 -> 岗位信号` |
| 岗位假设 | `target-roles.csv` | 生成 3-5 个可验证的岗位方向，不做人格算命 |
| JD 标准化 | `jobs.jsonl` | 整理用户提供的真实 JD、截图、链接和导出表 |
| 岗位匹配 | `job-matches.csv` | 按证据、硬性条件、兴趣、现实约束和风险初筛岗位 |
| 简历优化 | `resume-review.md` | 每条建议都回到真实经历，缺证据内容标记 `needs_proof` |
| 面试训练 | `interview-story-bank.md` | 训练自我介绍、项目回答、追问和风险表达 |
| 投递跟踪 | `application-tracker.csv` | 记录投递、回复、面试、拒信和复盘 |

## What It Will Not Do

Job OK 不是“自动投递神器”：

- 不编造经历；
- 不承诺 offer；
- 不自动投递；
- 不自动私信 HR；
- 不批量爬取招聘平台；
- 不绕过登录、验证码或平台限制；
- 不替企业做候选人排名或招聘决策。

## Quick Start

### 1. 让 Agent 帮你安装

在 Codex、Claude Code 或其他支持 Skill 的 Agent 里直接说：

```text
帮我安装这个 Skill：https://github.com/GresonKwan/JobOK
```

Agent 会把仓库安装到对应的本地 Skill 目录。安装完成后，重启你的 Agent 或新开会话：

```text
$job-ok
我是应届生，目标是深圳的 AI 应用实习/产品运营实习。
我会上传简历，并粘贴 3 个真实 JD。
请先问我必要问题，再帮我建立求职案例目录。
```

### 2. 手动安装备用

如果你的 Agent 不能自动安装，可以按所用工具的 Skill 目录手动 clone。Codex 示例：

```bash
git clone https://github.com/GresonKwan/JobOK.git ~/.codex/skills/job-ok
```

也可以下载 ZIP，解压后把整个文件夹复制到对应 Skill 目录。Codex 示例：

```text
~/.codex/skills/job-ok
```

Claude Code、Codex 和项目级安装说明见 [docs/install-cn.md](docs/install-cn.md)。

### 3. 项目级安装备用

如果你只想在当前项目启用：

```bash
git clone https://github.com/GresonKwan/JobOK.git .agents/skills/job-ok
```

## Usage Examples

### 1. 挖掘优势

```text
$job-ok
请围绕我的课程项目、实习、社团、兼职、自学和失败经历追问。
每个优势都要写清楚：证据、行为、能力、岗位信号和缺失证据。
```

### 2. 匹配岗位

```text
$job-ok
这里有 5 个真实 JD，请整理成 jobs.jsonl，并输出 job-matches.csv。
低于 60 分的岗位只放观察池，不建议投递。
```

### 3. 优化简历

```text
$job-ok
基于这个目标 JD，帮我做 resume-review.md。
不要编经历；缺少证据的内容标记 needs_proof。
```

### 4. 训练面试

```text
$job-ok
我先发一段自我介绍。
请检查结构、证据、岗位关联、废话和风险表达。
一次只问我一个追问问题。
```

## Case Folder

Job OK 默认会创建：

```text
job-search-cases/<yyyy-mm-dd-user-slug>/
├── brief.yaml
├── raw/
│   ├── resume/
│   └── job-posts/
├── profile.yaml
├── experience-assets.md
├── strengths.md
├── target-roles.csv
├── jobs.jsonl
├── job-matches.csv
├── resume-review.md
├── resume-versions/
├── interview-story-bank.md
├── interview-practice.md
├── application-tracker.csv
└── review-log.md
```

## Optional Dependencies

基础使用不需要安装依赖。只有解析 PDF/DOCX 简历时才需要：

```bash
python3 -m pip install -r requirements-optional.txt
```

国内网络可使用镜像：

```bash
python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-optional.txt
```

## Repository Structure

```text
.
├── SKILL.md
├── agents/openai.yaml
├── references/
├── assets/templates/
├── scripts/
├── examples/quick-start/
└── docs/
```

## Docs

- [安装说明](docs/install-cn.md)
- [使用指南](docs/usage-cn.md)
- [安全边界](docs/safety-cn.md)
- [FAQ](docs/faq-cn.md)
- [贡献说明](CONTRIBUTING.md)
- [更新记录](CHANGELOG.md)

## Safety

用户可以粘贴 Boss 直聘、猎聘、领英、学校就业网等来源的 JD，也可以上传截图、导出表或浏览器可见页面。

Job OK 只整理和分析用户授权提供的信息，不做后台批量抓取，不自动投递，不自动联系招聘方。

任何投递、私信、简历提交或平台操作，都应由用户自己确认和执行。

## License

MIT
