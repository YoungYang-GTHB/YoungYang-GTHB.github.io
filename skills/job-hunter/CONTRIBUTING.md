# Contributing

欢迎提交 issue 和 pull request。

优先接受这几类贡献：

- 更清楚的中文求职流程模板；
- 更稳健的 JD 标准化脚本；
- 更好的简历真实性检查规则；
- 更适合国内招聘平台输入格式的示例；
- 安全边界和反滥用规则补充。

不接受：

- 自动海投；
- 绕过招聘平台限制；
- 伪造经历；
- 承诺 offer；
- 企业侧候选人排名或录用建议。

提交前请至少运行：

```bash
python3 scripts/normalize_jobs.py --input examples/quick-start/jobs.md --output /tmp/job-ok-jobs.jsonl --source-type user_paste
```

如果修改了 `SKILL.md`，请用 Skill 校验器检查 frontmatter。
