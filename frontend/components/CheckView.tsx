"use client";

import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { LanguageSelect, useLanguage } from "@/components/LanguageSelect";
import { RedFlagSummary, UrlReport } from "@/components/ScamCheck";
import { checkMessage, checkUrl } from "@/lib/api";
import type { RedFlagReport, UrlAnalysis } from "@/lib/types";

type Mode = "message" | "url";

const SAMPLE_MESSAGE =
  "Dear Customer, your SBI account will be blocked within 24 hours. Update your KYC immediately at http://sbi-kyc-update.xyz/login and share the OTP sent to you.";
const SAMPLE_URL = "https://hdfcbank.com.secure-login.top/verify";

export function CheckView() {
  const params = useSearchParams();
  const [mode, setMode] = useState<Mode>(params.get("mode") === "url" ? "url" : "message");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [useLlm, setUseLlm] = useState(false);
  const [language, setLanguage] = useLanguage();
  const [report, setReport] = useState<RedFlagReport | null>(null);
  const [urlResult, setUrlResult] = useState<UrlAnalysis | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      if (mode === "message") setReport(await checkMessage(text.trim(), useLlm, language));
      else setUrlResult(await checkUrl(url.trim()));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };
  const value = mode === "message" ? text : url;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-2xl font-bold text-white">Check a suspicious message or link</h1>
      <p className="mt-1 text-sm text-slate-400">
        Both checks use fixed, explainable rules. Nothing is sent to the link — it is never opened or fetched. A result with
        no warning signs does not prove something is safe.
      </p>

      <div role="tablist" aria-label="Check type" className="mt-5 flex gap-1.5">
        {(["message", "url"] as const).map((m) => (
          <button key={m} role="tab" type="button" aria-selected={mode === m} onClick={() => setMode(m)}
            className={`btn px-3 py-1.5 text-xs ${mode === m ? "bg-signal text-ink-950" : "border border-ink-600 bg-ink-800 text-slate-300 hover:text-white"}`}>
            {m === "message" ? "Message (SMS / WhatsApp / email / chat)" : "Link (URL)"}
          </button>
        ))}
      </div>

      <form className="panel mt-3 space-y-3 p-4" onSubmit={(e) => { e.preventDefault(); if (value.trim()) void run(); }}>
        {mode === "message" ? (
          <>
            <label htmlFor="msg" className="text-xs text-slate-400">Paste the message exactly as you received it</label>
            <textarea id="msg" rows={6} maxLength={6000} value={text} onChange={(e) => setText(e.target.value)}
              className="w-full resize-y rounded-md border border-ink-600 bg-ink-950 p-2 text-sm text-white focus:border-signal focus:outline-none" />
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
              <label className="flex items-center gap-1.5">
                <input type="checkbox" checked={useLlm} onChange={(e) => setUseLlm(e.target.checked)} />
                Reword explanations with the language model (highlights still come only from rules)
              </label>
              {useLlm && <LanguageSelect value={language} onChange={setLanguage} />}
              <button type="button" className="underline" onClick={() => setText(SAMPLE_MESSAGE)}>use sample</button>
            </div>
          </>
        ) : (
          <>
            <label htmlFor="url" className="text-xs text-slate-400">Paste the link — don&apos;t open it</label>
            <input id="url" value={url} maxLength={2048} onChange={(e) => setUrl(e.target.value)} spellCheck={false}
              className="w-full rounded-md border border-ink-600 bg-ink-950 p-2 font-mono text-sm text-white focus:border-signal focus:outline-none" />
            <button type="button" className="text-xs text-slate-400 underline" onClick={() => setUrl(SAMPLE_URL)}>use sample</button>
          </>
        )}
        <div><button type="submit" className="btn-primary" disabled={busy || !value.trim()}>{busy ? "Checking…" : "Check"}</button></div>
        {error && <p className="text-sm text-danger">{error}</p>}
      </form>

      <div className="mt-4">
        {mode === "message" && report && <RedFlagSummary report={report} />}
        {mode === "url" && urlResult && <div className="panel p-4"><UrlReport analysis={urlResult} /></div>}
      </div>
    </div>
  );
}
