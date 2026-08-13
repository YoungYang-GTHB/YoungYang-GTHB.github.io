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

### 云端服务器 / 纯终端登录

服务器无需安装或打开 Chrome。先在 SSH 终端显示微信二维码并扫码：

```bash
python3 scripts/fetch_jobs.py --wechat-login
```

登录会话以 `0600` 权限保存在本地 `.session.json`（已加入 `.gitignore`）。随后只拉取当前提前批：

```bash
python3 scripts/fetch_jobs.py --nav 61 --phase 提前批 --full-sync
```

短期 access token 过期时工具会自动调用平台当前使用的刷新接口；整个微信会话失效后才需要重新扫码。

### 当前项目的统一工作台

项目内所有岗位同步、短名单、投递前确认和成功落档统一使用 `jobctl.py`，不再分别手工维护截图、Markdown 和 CSV：

```bash
# 校验唯一数据源，并查看当前投递统计
python3 skills/job-hunter/scripts/jobctl.py validate
python3 skills/job-hunter/scripts/jobctl.py status

# 同步当前提前批，并按具身智能主线查看前 20 个岗位
python3 skills/job-hunter/scripts/jobctl.py sync --phase 提前批
python3 skills/job-hunter/scripts/jobctl.py shortlist --phase 提前批 --limit 20

# 推荐：一条命令完成增量同步、历史排除和高匹配短名单输出
python3 skills/job-hunter/scripts/jobctl.py scan \
  --phase 提前批 --min-score 35 --limit 15

# 若服务器直连失效，导入浏览器扩展导出的可见岗位数据
python3 skills/job-hunter/scripts/jobctl.py sync \
  --phase 提前批 \
  --browser-export imports/YYYY-MM-DD_offer-nav61_raw.jsonl
```

统一账本位于 `career/求职投递/2027届/data/applications.yaml`，`投递汇总.md`、旧 CSV 追踪器和已投 URL 去重状态均由它生成或回填。历史数据需要恢复时执行：

```bash
python3 skills/job-hunter/scripts/jobctl.py reconcile
```

账本中的 `active_phase` 是硬门禁。当前为提前批；以后阶段切换时只需执行：

```bash
python3 skills/job-hunter/scripts/jobctl.py set-phase 秋招
```

与当前批次不同的岗位无法进入提交流程。政策为 `unknown`、`affects_formal` 或仅有往届证据的岗位会自动标为暂缓；只有当届明确安全，或本人明确批准例外后，才能通过 `preflight`。

历史已经明确决定“不投”的岗位写入长期排除库
`career/求职投递/2027届/data/job_exclusions.yaml`。扫描器会先过滤排除库，避免反复展示、反复消耗模型上下文。推荐使用命令维护，而不是直接改 YAML：

```bash
python3 skills/job-hunter/scripts/jobctl.py exclude add \
  --id example-low-fit \
  --company 示例公司 \
  --position-keyword RAG \
  --phase 提前批 \
  --reason '与具身智能主线和嵌入式支线匹配度低'

python3 skills/job-hunter/scripts/jobctl.py exclude list --phase 提前批
python3 skills/job-hunter/scripts/jobctl.py exclude remove example-low-fit
```

排除规则支持公司、岗位关键词、岗位 ID、URL、阶段和到期日。岗位 ID / URL 适合精确排除；公司 + 岗位关键词适合过滤同类重复岗位。若只是提前批暂不投，应填写 `--phase 提前批`，避免误伤后续秋招的新岗位。

新岗位先创建草稿并查看最终快照：

```bash
python3 skills/job-hunter/scripts/jobctl.py prepare \
  --id company-job-id \
  --company 公司名 \
  --position 岗位名 \
  --phase 提前批 \
  --policy-status current_year_safe \
  --resume public/resume.pdf
python3 skills/job-hunter/scripts/jobctl.py preflight company-job-id
```

验证码和招聘网站的最终提交仍由本人确认。网页显示投递成功后，使用 `preflight` 输出的令牌一次性落档：

```bash
python3 skills/job-hunter/scripts/jobctl.py record-applied company-job-id \
  --confirmation 'CONFIRM:company-job-id:……' \
  --verified
```

这样可以防止重复投递、错用简历、混投批次或把“页面已填写”误记为“投递成功”。

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

浏览器已经把 Offer 情报局当前可见导航落档后，可以只导入当前招聘阶段：

```bash
python3 scripts/import_offer_export.py \
  --input imports/YYYY-MM-DD_offer-nav61_raw.jsonl \
  --phase 提前批
```

该流程不要求把网页 token 复制到本地；它只处理用户在浏览器中主动同步的岗位文件。阶段不明确的岗位不会进入提前批候选池。

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
