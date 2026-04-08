import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: {
    default: "BlogAI — AI-Powered Content Hub",
    template: "%s | BlogAI",
  },
  description:
    "High-quality, SEO-optimised blog articles generated daily. Expert insights on technology, development, and industry trends.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://example.com"
  ),
  openGraph: {
    title: "BlogAI — AI-Powered Content Hub",
    description: "High-quality, SEO-optimised blog articles generated daily.",
    siteName: "BlogAI",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "BlogAI",
    description: "High-quality, SEO-optimised blog articles generated daily.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="min-h-screen animated-gradient antialiased" suppressHydrationWarning>
        <Navbar />
        <main className="pt-16 min-h-screen">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
