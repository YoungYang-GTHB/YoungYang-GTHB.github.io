# 郭睢阳个人简历网站

基于 Next.js 16 + TypeScript + Tailwind CSS v4 构建的现代化个人简历网站。

## 🚀 快速启动

### 1. 安装依赖

首次使用需要安装依赖：

```bash
npm install
```

### 2. 启动开发服务器

日常开发使用开发模式（支持热重载）：

```bash
npm run dev
```

启动后访问：**http://localhost:3000**

### 3. 生产环境运行

构建并启动生产服务器：

```bash
npm run build
npm start
```

---

## 📁 项目结构

```
resume-website/
├── content/
│   └── resume.yaml          # 简历数据配置（修改这里更新内容）
├── public/
│   ├── profile/             # 个人照片
│   └── projects/            # 项目图片/视频/PDF
├── src/
│   ├── app/                 # 页面路由
│   ├── components/          # React 组件
│   ├── lib/                 # 工具函数
│   └── types/               # TypeScript 类型
├── package.json
└── README.md
```

---

## ✏️ 修改简历内容

编辑 `content/resume.yaml` 文件即可更新简历信息，无需修改代码。

添加项目资料时，将文件放入 `public/projects/` 目录，然后在 YAML 中引用路径。

---

## 🛠️ 常用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器（日常使用） |
| `npm run build` | 生产构建 |
| `npm start` | 启动生产服务器 |
| `npm run lint` | 代码检查 |

---

## 📦 环境要求

- Node.js 18+
- npm 或 pnpm

---

## 🌐 部署

推荐部署到 **Vercel**：

1. 在 [vercel.com](https://vercel.com) 导入此仓库
2. 自动构建部署

---

## 📄 许可证

MIT
