import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "CyberSahayak — Cyber Crime Complaint & Awareness Assistant",
  description: "Understand scams, preserve evidence, draft complaints and learn to stay safe online.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 btn-primary">
          Skip to content
        </a>
        <header className="sticky top-0 z-40 border-b border-ink-700 bg-ink-950/85 backdrop-blur">
          <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3" aria-label="Main">
            <Link href="/" className="flex items-center gap-2 font-semibold text-white">
              <span aria-hidden className="grid h-8 w-8 place-items-center rounded-lg bg-signal/15 font-mono text-signal ring-1 ring-signal/40">
                ⛨
              </span>
              CyberSahayak
              <span className="hidden font-mono text-xs font-normal text-slate-400 sm:inline">/ complaint &amp; awareness assistant</span>
            </Link>
            <div className="flex items-center gap-2">
              <Link href="/" className="btn-ghost hidden sm:inline-flex">Dashboard</Link>
              <Link href="/check" className="btn-ghost">Check message / link</Link>
              <Link href="/assistant" className="btn-primary">Open assistant</Link>
            </div>
          </nav>
        </header>
        <main id="main">{children}</main>
      </body>
    </html>
  );
}
