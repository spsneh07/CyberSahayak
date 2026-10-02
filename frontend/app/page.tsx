"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { QuickActionGrid } from "@/components/QuickActions";
import { getHealth, getMeta } from "@/lib/api";
import type { Meta } from "@/lib/types";

const PIPELINE = ["Understand", "Extract", "Classify", "Retrieve (RAG)", "Explain", "Guide", "Complaint & awareness"];

export default function Dashboard() {
  const router = useRouter();
  const [meta, setMeta] = useState<Meta | null>(null);
  const [health, setHealth] = useState<{ ok: boolean; chunks?: number; llm?: string } | null>(null);

  useEffect(() => {
    getMeta().then(setMeta).catch(() => setMeta(null));
    getHealth()
      .then((h) => setHealth({ ok: h.status === "ok", chunks: h.knowledge_chunks, llm: h.llm_provider }))
      .catch(() => setHealth({ ok: false }));
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <section className="grid gap-8 lg:grid-cols-[1.3fr_1fr] lg:items-center">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.25em] text-signal">Cyber crime help desk</p>
          <h1 className="mt-3 text-3xl font-bold leading-tight text-white sm:text-5xl">
            Scammed, hacked or unsure? <span className="text-signal">Get clear next steps.</span>
          </h1>
          <p className="mt-4 max-w-xl text-slate-300">
            Describe what happened in your own words. The assistant structures your incident, identifies the likely type of
            cybercrime, retrieves guidance from trusted sources, and helps you preserve evidence and draft a formal complaint.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/assistant?action=report" className="btn-primary px-5 py-3 text-base">Report an incident</Link>
            <Link href="/assistant?action=check" className="btn-ghost px-5 py-3 text-base">Check a suspicious message</Link>
          </div>
        </div>
        <div className="panel p-5">
          <h2 className="panel-title">System status</h2>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-400">Backend</dt>
              <dd className={health?.ok ? "text-safe" : "text-danger"}>{health === null ? "checking…" : health.ok ? "online" : "offline"}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-400">AI provider</dt>
              <dd className="font-mono">{meta?.llm_provider ?? "—"}{meta?.llm_provider === "mock" && <span className="ml-2 text-warn">(offline heuristic mode)</span>}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-400">Knowledge chunks indexed</dt>
              <dd className="font-mono">{health?.chunks ?? "—"}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-400">Categories supported</dt>
              <dd className="font-mono">{meta ? meta.categories.length - 1 : "—"}</dd></div>
          </dl>
          <ol className="mt-5 flex flex-wrap items-center gap-1 font-mono text-[11px] text-slate-400" aria-label="Analysis pipeline">
            {PIPELINE.map((p, i) => (
              <li key={p} className="flex items-center gap-1">
                <span className="rounded border border-ink-600 bg-ink-800 px-1.5 py-0.5">{p}</span>
                {i < PIPELINE.length - 1 && <span aria-hidden className="text-signal">→</span>}
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="mt-12" aria-labelledby="qa-title">
        <h2 id="qa-title" className="mb-4 text-lg font-semibold text-white">What do you need help with?</h2>
        <QuickActionGrid onPick={(a) => router.push(`/assistant?action=${a.id}`)} />
      </section>

      <section className="mt-12 grid gap-4 md:grid-cols-3">
        {[
          ["Act fast on money loss", "If money left your account, contact your bank through official channels and report the fraud immediately — speed matters for holding funds."],
          ["Never share OTP / UPI PIN", "No bank, police or government agency asks for OTPs, PINs or passwords. You never need a UPI PIN to receive money."],
          ["Keep the evidence", "Don't delete chats, SMS or call logs. Screenshot them with dates and sender details visible."],
        ].map(([t, d]) => (
          <div key={t} className="panel p-4">
            <h3 className="font-semibold text-white">{t}</h3>
            <p className="mt-1 text-sm text-slate-400">{d}</p>
          </div>
        ))}
      </section>

      <p className="mt-12 border-t border-ink-700 pt-4 text-xs text-slate-500">
        {meta?.disclaimer ??
          "This assistant provides educational cybersecurity guidance and complaint-drafting assistance. It is not a substitute for law enforcement, legal advice, or professional cybersecurity investigation."}
      </p>
    </div>
  );
}
