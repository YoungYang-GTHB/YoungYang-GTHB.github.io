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
| `main.tex` | **当前工作版本**，基于 resume-photo 定制 |
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
```

Overleaf: 上传整个 `templates/resume/` 目录，主文件选 `main.tex`，编译器选 `XeLaTeX`。

## 定制记录

- [ ] 照片替换为个人证件照
- [ ] 个人信息替换为实际内容
- [ ] 添加二维码支持 (`\usepackage{qrcode}`)
- [ ] 配色调整（西工大蓝 #00529b）
