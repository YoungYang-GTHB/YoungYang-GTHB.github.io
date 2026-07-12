import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "郭睢阳 - 具身智能工程师",
  description: "西北工业大学控制工程硕士，面向具身智能的机器人研发工程师。聚焦机器人导航、SLAM 与智能交互，具备从机械、电路到嵌入式与上位机的全流程落地能力；参与国家级重点课题，拥有 6 项专利与 2 项软件著作权。",
  keywords: ["具身智能", "机器人", "ROS", "SLAM", "导航", "嵌入式开发", "STM32", "深度学习", "西北工业大学", "简历"],
  authors: [{ name: "郭睢阳" }],
  openGraph: {
    title: "郭睢阳 - 具身智能工程师",
    description: "面向具身智能的机器人研发工程师 · 西北工业大学控制工程硕士",
    type: "website",
    locale: "zh_CN",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
