import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { getResumeData } from "@/lib/resume";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export function generateMetadata(): Metadata {
  const { personal } = getResumeData();
  const title = `${personal.name} · ${personal.title}`;
  const description = personal.summary.trim().replace(/\s+/g, " ");

  return {
    title,
    description,
    keywords: ["VLA", "Embodied AI", "Robot Learning", "ROS2", "Robotics", "Embedded Systems"],
    authors: [{ name: personal.name }],
    openGraph: {
      title,
      description,
      type: "profile",
      locale: "zh_CN",
    },
  };
}

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
