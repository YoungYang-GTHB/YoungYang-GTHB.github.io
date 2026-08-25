# YoungYang-GTHB.github.io 环境部署与配置指南

## 一、环境依赖

### 1.1 运行时环境

| 组件 | 最低版本 | 验证命令 | 安装方式 |
|------|----------|----------|----------|
| **Node.js** | ≥20.9.0 | `node --version` | [nodesource](https://deb.nodesource.com/) 或 `conda install -c conda-forge nodejs=22` |
| **npm** | ≥10 | `npm --version` | 随 Node.js 自带 |
| **Python** | ≥3.9 | `python3 --version` | 系统自带或 `conda install python=3.12` |
| **TeX Live** | ≥2021 (推荐 2026) | `xelatex --version` | [TUG 官方安装器](https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz) |
| **Chrome/Edge** | 最新版 | — | https://www.google.com/chrome/ |

### 1.2 TeX Live 安装（Linux）

```bash
wget https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz
tar xzf install-tl-unx.tar.gz
cd install-tl-*
sudo perl install-tl --scheme=full --no-interaction

# 配置环境变量（追加到 ~/.bashrc）
echo 'export PATH=/usr/local/texlive/2026/bin/x86_64-linux:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### 1.3 Node.js 安装（Ubuntu 24.04）

```bash
# NodeSource 官方源
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# 验证
node --version  # 应显示 v22.x
```

---

## 二、克隆项目

```bash
git clone https://github.com/YoungYang-GTHB/YoungYang-GTHB.github.io.git
cd YoungYang-GTHB.github.io
```

---

## 三、安装依赖

### 3.1 npm 依赖

```bash
npm install
```

国内网络慢可先切换镜像：
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### 3.2 Python 依赖

```bash
python3 -m pip install pyyaml requests
```

### 3.3 验证

```bash
# 网站构建
npm run build

# LaTeX 简历编译
cd templates/resume
xelatex main.tex && xelatex main.tex

# Python 岗位拉取
cd skills/job-hunter
python3 scripts/fetch_jobs.py --check-token  # 需先配置 token
```

---

## 四、配置 Chrome 扩展

### 4.1 加载 form-filler 扩展

1. Chrome → 地址栏输入 `chrome://extensions/`
2. 右上角开启 **开发者模式**
3. 点击 **加载已解压的扩展程序**
4. 选择 `tools/form-filler/` 目录
5. 扩展图标会出现在 Chrome 工具栏

### 4.2 配置 AI 模型（可选，提升填表准确率）

1. 点击扩展图标 → **模型配置**
2. 填入 DeepSeek API Key（或任意 OpenAI 兼容接口）
3. 如不配置，扩展使用本地规则匹配（基础可用）

---

## 五、外部账号准备

### 5.1 offer情报局（岗位数据源）

1. 浏览器打开 https://offerqingbaoju.cn
2. 微信扫码注册/登录
3. 登录后按 `F12` → **Application** → **Local Storage** → `offerqingbaoju.cn`
4. 复制 `token` 的值
5. 在本项目中保存：

```bash
cd skills/job-hunter
python3 scripts/fetch_jobs.py --save-token "你的token值"
```

> Token 有效期约 24 小时。过期后需重新从浏览器提取。

### 5.2 可选账号

| 平台 | 用途 | 是否必需 |
|------|------|----------|
| GitHub | 代码托管 | 推荐 |
| DeepSeek API | form-filler AI 识图 | 可选 |
| Cloudflare Pages | 个人网站部署 | 可选 |
| Vercel | 个人网站备选部署 | 可选 |

---

## 六、私有个人数据

### 6.1 结构化数据（简历生成的数据源）

真实数据存放在私有子模块 `career/site/content/resume.yaml`。公开仓库仅提供 `examples/resume.example.yaml` 匿名示例。具有私有仓库权限时执行：

```bash
./scripts/prepare-private-site.sh
RESUME_DATA_PATH=content/resume.public.yaml npm run dev
```

结构化数据包含：

- `personal` — 基本信息（姓名、邮箱、电话、地址、GitHub 等）
- `education` — 教育经历（学校、专业、GPA、排名）
- `skills` — 技能（编程、嵌入式、OS、工具分类 + 掌握程度）
- `projects` — 项目经历（标题、技术栈、成果要点）
- `experience` — 实习/培训经历
- `awards` — 竞赛获奖
- `honors` — 荣誉
- `patents` — 专利
- `certifications` — 证书

### 6.2 个人知识库

个人文档位于私有子模块 `career/个人知识库/`，不提交到公开主仓库。

```
career/个人知识库/
├── areas/         # 活跃：简历/项目/求职
├── resources/     # 参考：证书/论文/竞赛
├── archive/       # 归档：旧项目/课程
├── raw/           # 原始记录
├── wiki/          # 精炼知识
└── schema/        # 结构化数据
```

### 6.3 LaTeX 简历

- 通用类与字体：`templates/resume/`
- 私有个人化源码：`career/resumes/sources/`
- 私有照片：`career/resumes/assets/photo.jpg`
- 编译：`./scripts/build-private-resumes.sh`

---

## 七、核心配置

### 7.1 岗位筛选配置

编辑 `skills/job-hunter/config.yaml`：

```yaml
filters:
  cities: [西安, 深圳, 北京, 上海, 成都]      # 目标城市
  industries: [机器人, 半导体, 自动, 汽车...]  # 目标行业
  exclude_industries: [教育, 金融, 房地产...]  # 排除行业
  graduation_year: "2027"
```

### 7.2 .gitignore 保护的敏感文件

以下文件包含个人信息，不进 git：

| 文件 | 内容 |
|------|------|
| `skills/job-hunter/.token` | offer情报局 API Token |
| `skills/job-hunter/state.json` | 岗位抓取状态 |
| `skills/job-hunter/records/` | 投递记录 |
| `output/` | 生成的简历 PDF 和岗位 JSONL |
| `content/resume.yaml` | 从私有子模块同步的本地个人数据 |
| `public/profile/`、`public/projects/`、`public/resume*.pdf` | 从私有子模块同步的本地展示产物 |
| `.npmrc` | npm 镜像配置 |

---

## 八、常用操作速查

```bash
# ─── 网站 ───
npm run dev                    # 本地开发服务器 http://localhost:3000
npm run build                  # 生产构建

# ─── 私有站点与简历 ───
./scripts/prepare-private-site.sh
RESUME_DATA_PATH=content/resume.public.yaml npm run dev
./scripts/build-private-resumes.sh

# ─── 岗位拉取 ───
cd skills/job-hunter
python3 scripts/fetch_jobs.py --save-token "<TOKEN>"   # 首次：保存 token
python3 scripts/fetch_jobs.py                          # 增量拉取
python3 scripts/fetch_jobs.py --full-sync              # 全量拉取
python3 scripts/fetch_jobs.py --dry-run                # 预览不写入
python3 scripts/fetch_jobs.py --stats                  # 状态统计

# ─── 表单填写 ───
python3 scripts/profile_mapper.py --compact > /tmp/profile.json
# 然后将 profile.json 粘贴到 Chrome form-filler 侧边栏

# ─── Claude Code Skills ───
# 在 CC 对话中直接调用：
# /resume-generator "机器人算法工程师"   → 生成针对性简历
# /job-hunter "帮我找今天的西安嵌入式岗"  → 拉取+筛选+匹配
```

---

## 九、部署个人网站（可选）

### Cloudflare Pages（推荐）

```bash
npm run build          # 输出到 out/
npm run deploy         # 或: npx wrangler pages deploy out
```

### Vercel

已配置 GitHub Actions，push 到 main 分支自动部署。需在仓库 Settings → Secrets 中配置：
- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

---

## 十、故障排查

| 问题 | 解决 |
|------|------|
| `node --version` < 20 | Node.js 版本过低，按 1.3 节升级 |
| `xelatex: command not found` | TeX Live 未安装或 PATH 未配置，按 1.2 节操作 |
| fetch_jobs.py 报 `Token 无效` | Token 已过期，重新从浏览器提取 |
| fetch_jobs.py 报网络错误 | 检查 `config.yaml` 中 `api.base_url` 是否正确 |
| form-filler 填表不准确 | 在模型配置中填入 DeepSeek API Key |
| `npm install` 报网络错误 | `npm config set registry https://registry.npmmirror.com` |
