import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 启用静态导出，输出纯 HTML 文件
  output: 'export',

  // 静态导出时禁用图片优化（使用普通 img 标签）
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
