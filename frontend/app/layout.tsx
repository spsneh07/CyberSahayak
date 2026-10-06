import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "CyberShield AI — Cyber Crime Complaint & Awareness Assistant",
  description: "Understand scams, preserve evidence, draft complaints and learn to stay safe online.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col">
        <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 btn-primary">
          Skip to content
        </a>

        {/* Independence notice: this is not a government service. */}
        <div className="bg-navy text-[12px] text-[#dbe4f3]">
          <p className="mx-auto max-w-7xl px-4 py-1.5">
            Independent student project — <strong className="text-paper">not a government website</strong>. To report officially,
            use the National Cyber Crime Reporting Portal (cybercrime.gov.in) or call 1930.
          </p>
        </div>

        <header className="sticky top-0 z-40 border-b-4 border-signal bg-paper shadow-sm">
          <nav className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-3" aria-label="Main">
            <Link href="/" className="flex items-center gap-3 text-white">
              <svg aria-hidden viewBox="0 0 64 64" className="h-10 w-10 shrink-0">
                <rect width="64" height="64" rx="12" fill="#0b2447" />
                <path d="M32 11 50 17.5V31c0 11.2-7.6 19.4-18 23-10.4-3.6-18-11.8-18-23V17.5Z" fill="#0b5cad" stroke="#ffffff" strokeWidth="3" strokeLinejoin="round" />
                <path d="M24 32.5 29.5 38 40.5 26.5" fill="none" stroke="#ffffff" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span className="leading-tight">
                <span className="block text-lg font-bold">CyberShield AI</span>
                <span className="block text-xs text-slate-400">Cyber crime help, evidence &amp; complaint assistant</span>
              </span>
            </Link>
            <div className="flex flex-wrap items-center gap-1">
              <Link href="/" className="rounded-md px-3 py-2 text-sm font-semibold text-slate-300 hover:bg-ink-800 hover:text-signal">Home</Link>
              <Link href="/check" className="rounded-md px-3 py-2 text-sm font-semibold text-slate-300 hover:bg-ink-800 hover:text-signal">Check message / link</Link>
              <Link href="/assistant" className="btn-primary">Get help now</Link>
            </div>
          </nav>
        </header>

        <main id="main" className="flex-1">{children}</main>

        <footer className="mt-10 bg-navy text-[13px] text-[#c9d6ea]">
          <div className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:grid-cols-3">
            <div>
              <p className="font-semibold text-paper">CyberShield AI</p>
              <p className="mt-1">An educational assistant built as a B.Tech Applied GenAI course project. It does not file complaints
                and is not affiliated with any government body.</p>
            </div>
            <div>
              <p className="font-semibold text-paper">Report officially</p>
              <ul className="mt-1 space-y-1">
                <li>National Cyber Crime Reporting Portal: <a className="underline" href="https://cybercrime.gov.in" target="_blank" rel="noreferrer">cybercrime.gov.in</a></li>
                <li>National cybercrime helpline: <strong className="text-paper">1930</strong></li>
                <li>Your local police station or cyber cell</li>
              </ul>
            </div>
            <div>
              <p className="font-semibold text-paper">Stay safe</p>
              <p className="mt-1">Never share OTPs, PINs or passwords. Keep all messages and screenshots as evidence.</p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
