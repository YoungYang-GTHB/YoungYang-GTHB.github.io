# 📦 Cloudflare Pages 部署指南

## ✅ 前置准备

1. **Cloudflare 账号**：访问 [dash.cloudflare.com](https://dash.cloudflare.com) 注册/登录
2. **GitHub 账号**：将项目推送到 GitHub 仓库

---

## 🚀 部署方式一：GitHub 集成（推荐）

### 步骤 1：推送代码到 GitHub

```bash
# 初始化 git（如果还没有）
git init
git add .
git commit -m "Initial commit"

# 关联远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/resume-website.git
git push -u origin main
```

### 步骤 2：在 Cloudflare 创建 Pages 项目

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com)
2. 左侧菜单 → **Pages** → **Create a project**
3. 选择 **Connect to Git**
4. 选择你的 `resume-website` 仓库

### 步骤 3：配置构建设置

| 设置项 | 值 |
|--------|-----|
| **Production branch** | `main` |
| **Build command** | `npm run build` |
| **Build output directory** | `out` |
| **Root directory** | `resume-website`（如果仓库根就是项目，留空） |

### 步骤 4：部署

点击 **Save and Deploy**，等待构建完成（约 2-5 分钟）

部署成功后会获得一个免费域名：
```
https://resume-website.你的用户名.pages.dev
```

---

## 🚀 部署方式二：命令行直接部署

### 步骤 1：安装 Wrangler CLI

```bash
npm install -g wrangler
```

### 步骤 2：登录 Cloudflare

```bash
wrangler login
```

会打开浏览器进行授权。

### 步骤 3：本地预览（可选）

```bash
npm run preview
```

访问 `http://localhost:8788` 预览效果。

### 步骤 4：部署到生产环境

```bash
npm run deploy
```

或手动执行：
```bash
npx wrangler pages deploy out
```

---

## 🌐 自定义域名（可选）

### 在 Cloudflare 配置：

1. 进入 Pages 项目 → **Custom domains**
2. **Add custom domain**
3. 输入你的域名（如 `www.guosuiyang.com`）
4. 按照提示配置 DNS（如果域名在 Cloudflare 管理，自动完成）

---

## ⚙️ 高级配置

### 设置环境变量

在 Cloudflare Dashboard → Pages → 你的项目 → **Settings** → **Environment variables**

### 配置重定向规则

创建 `public/_headers` 和 `public/_redirects` 文件：

```
# public/_headers
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
```

---

## 📊 免费额度

| 资源 | 额度 |
|------|------|
| 带宽 | 无限 |
| 请求数 | 无限 |
| 存储空间 | 无限 |
| 构建分钟数 | 500 分钟/天 |

---

## 🔧 常见问题

### Q: 构建失败怎么办？

查看构建日志，常见原因：
- Node.js 版本过低（需要 18+）
- 依赖安装失败（尝试删除 `node_modules` 重新安装）

### Q: 图片无法显示？

确保图片文件在 `public/` 目录下，路径以 `/` 开头。

### Q: 如何更新部署？

- GitHub 集成：推送代码后自动重新部署
- 命令行：重新运行 `npm run deploy`

---

## 📈 访问统计

在 Cloudflare Dashboard → Pages → 你的项目 → **Analytics** 查看访问数据。

---

**部署成功后，将你的 .pages.dev 域名分享给朋友吧！** 🎉
