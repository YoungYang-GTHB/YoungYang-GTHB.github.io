# 安装说明

Job OK 是一个本地 Skill。最简单的方式是让 Codex、Claude Code 或其他支持 Skill 的 Agent 直接安装。

## 推荐方式：让 Agent 安装

在 Codex、Claude Code 或其他支持 Skill 的 Agent 里说：

```text
帮我安装这个 Skill：https://github.com/GresonKwan/JobOK
```

安装完成后，重启你的 Agent 或新开会话：

```text
$job-ok
```

如果你的 Agent 不能自动安装，再使用下面的手动方式。

## 手动个人级安装

不同 Agent 的 Skill 目录可能不同。下面是常见示例。

### Codex

```bash
git clone https://github.com/GresonKwan/JobOK.git ~/.codex/skills/job-ok
```

如果目录已存在，先备份旧版本：

```bash
mv ~/.codex/skills/job-ok ~/.codex/skills/job-ok.backup
git clone https://github.com/GresonKwan/JobOK.git ~/.codex/skills/job-ok
```

### Claude Code

如果你使用 Claude Code，请按 Claude Code 当前版本的 Skill 目录安装。常见个人级路径类似：

```bash
git clone https://github.com/GresonKwan/JobOK.git ~/.claude/skills/job-ok
```

如果你的客户端使用不同目录，请以该客户端的 Skill 安装说明为准。

## 手动项目级安装

进入你的项目目录：

```bash
mkdir -p .agents/skills
git clone https://github.com/GresonKwan/JobOK.git .agents/skills/job-ok
```

项目级安装只在当前项目内生效，适合团队项目或课程项目。

## 使用安装脚本

在仓库根目录运行：

```bash
python3 scripts/install_local.py
```

安装到当前项目：

```bash
python3 scripts/install_local.py --project
```

覆盖已有安装：

```bash
python3 scripts/install_local.py --force
```

## 国内网络建议

- GitHub clone 慢时，可以下载 ZIP 后手动复制。
- PDF/DOCX 解析依赖是可选的，不影响基础使用。
- 安装可选依赖时可以使用清华 PyPI 镜像：

```bash
python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-optional.txt
```

## 验证

重启你的 Agent 或新开会话后输入：

```text
$job-ok
```

如果能触发 Skill，说明安装成功。
