# LaTeX 简历模板

## 来源

基于 [adongwanai/LLM-Resume-Template](https://github.com/adongwanai/LLM-Resume-Template)
- 原作者: [@adongwanai](https://github.com/adongwanai)
- 原始仓库: `https://github.com/adongwanai/LLM-Resume-Template.git`
- 许可证: CC BY 4.0
- 原始模板基于 [liweitianux/resume](https://github.com/liweitianux/resume) 项目修改

重新拉取: `git clone https://github.com/adongwanai/LLM-Resume-Template.git`

## 文件说明

| 文件 | 说明 |
|------|------|
| `main.tex` | **VLA / 具身智能中文版** → `public/resume-vla-zh.pdf` |
| `main-en.tex` | **VLA / Embodied AI English** → `public/resume-vla-en.pdf` |
| `main-embedded.tex` | **嵌入式开发中文版** → `public/resume-embedded-zh.pdf` |
| `main-embedded-en.tex` | **Embedded Systems English** → `public/resume-embedded-en.pdf` |
| `resume-photo.cls` | 带头像版文档类，基于 ctexart |
| `fontawesome5/` | FontAwesome 5 图标字体 |
| `_originals/` | 原始模板备份（未修改） |
| `_originals/resume-photo_orig.tex` | 原始带头像简历 |
| `_originals/resume-photo_orig.cls` | 原始带头像文档类 |
| `_originals/resume-zh_orig.tex` | 原始无头像中文简历 |
| `_originals/resume_orig.cls` | 原始无头像文档类 |
| `_originals/resume-model_orig.tex` | 原始占位符模板 |

## 编译

```bash
xelatex main.tex
xelatex main.tex  # 编译两次
xelatex main-embedded.tex
xelatex main-embedded.tex  # 编译两次
xelatex main-en.tex
xelatex main-en.tex
xelatex main-embedded-en.tex
xelatex main-embedded-en.tex
```

公开目录中的 `resume.pdf`、`resume-en.pdf` 和 `resume-embedded.pdf` 为兼容旧投递记录与网页链接保留的别名；人工上传时优先使用带方向和语言标识的规范文件名。

Overleaf: 上传整个 `templates/resume/` 目录，主文件选 `main.tex`，编译器选 `XeLaTeX`。

## 定制记录

- [ ] 照片替换为个人证件照
- [ ] 个人信息替换为实际内容
- [ ] 添加二维码支持 (`\usepackage{qrcode}`)
- [ ] 配色调整（西工大蓝 #00529b）
