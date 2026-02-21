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
  title: "郭睢阳 - 机器人工程师简历",
  description: "西北工业大学机器人工程师，专注于机器人系统设计与控制，具备从机械设计、电路设计到嵌入式软件和上位机开发的全流程研发能力。",
  keywords: ["机器人工程师", "ROS", "嵌入式开发", "STM32", "西北工业大学", "简历"],
  authors: [{ name: "郭睢阳" }],
  openGraph: {
    title: "郭睢阳 - 机器人工程师简历",
    description: "西北工业大学机器人工程师个人简历",
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
