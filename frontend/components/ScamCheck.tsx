"use client";

import { useState } from "react";
import type { RedFlagReport, RedFlagSpan, Severity, UrlAnalysis } from "@/lib/types";

const CATEGORY_STYLE: Record<string, string> = {
  credential_request: "bg-danger/25 ring-danger/60",
  payment_request: "bg-danger/25 ring-danger/60",
  remote_access: "bg-danger/25 ring-danger/60",
  urgency_threat: "bg-warn/25 ring-warn/60",
  impersonation: "bg-warn/25 ring-warn/60",
  personal_info_request: "bg-warn/25 ring-warn/60",
  too_good_to_be_true: "bg-warn/20 ring-warn/50",
  suspicious_link: "bg-signal/20 ring-signal/60",
};

const RISK_STYLE: Record<string, string> = {
  high: "text-danger", medium: "text-warn", low: "text-safe", none_found: "text-slate-300", invalid: "text-slate-400",
};
const RISK_LABEL: Record<string, string> = {
  high: "High", medium: "Medium", low: "Low", none_found: "No known patterns matched", invalid: "Not a valid URL",
};
const SEVERITY_STYLE: Record<Severity, string> = {
  high: "text-danger", medium: "text-warn", low: "text-slate-300", info: "text-slate-500",
};

/** Split the text at span boundaries so overlapping spans render as nested highlights without losing characters. */
function segments(text: string, spans: RedFlagSpan[]) {
  const cuts = new Set<number>([0, text.length]);
  spans.forEach((s) => { cuts.add(s.start); cuts.add(s.end); });
  const points = [...cuts].sort((a, b) => a - b);
  return points.slice(0, -1).map((start, i) => {
    const end = points[i + 1] ?? text.length;
    return { start, end, text: text.slice(start, end), covering: spans.filter((s) => s.start <= start && s.end >= end) };
  });
}

export function HighlightedMessage({ report }: { report: RedFlagReport }) {
  const [active, setActive] = useState<number | null>(null);
  return (
    <div className="space-y-3">
      <p className="whitespace-pre-wrap break-words rounded-lg bg-ink-950 p-3 text-sm leading-7 text-slate-200 ring-1 ring-ink-600">
        {segments(report.text, report.spans).map((seg) => {
          const first = seg.covering[0];
          if (!first) return <span key={seg.start}>{seg.text}</span>;
          const idx = report.spans.indexOf(first);
          return (
            <mark key={seg.start} title={seg.covering.map((s) => s.label).join(", ")}
              onMouseEnter={() => setActive(idx)} onFocus={() => setActive(idx)} tabIndex={0}
              className={`rounded px-0.5 text-white ring-1 ${CATEGORY_STYLE[first.category] ?? "bg-warn/20 ring-warn/50"} ${active === idx ? "outline outline-2 outline-white/60" : ""}`}>
              {seg.text}
            </mark>
          );
        })}
      </p>
      <ol className="space-y-2" aria-label="Red flags found">
        {report.spans.map((s, i) => (
          <li key={`${s.start}-${s.end}-${s.category}`} onMouseEnter={() => setActive(i)}
            className={`rounded-lg border p-2.5 text-sm ${active === i ? "border-signal/60 bg-ink-800" : "border-ink-600"}`}>
            <p className="flex flex-wrap items-center gap-2">
              <span className={`chip ring-1 ${CATEGORY_STYLE[s.category] ?? ""}`}>{s.label}</span>
              <q className="break-all font-mono text-xs text-white">{s.text}</q>
            </p>
            <p className="mt-1 text-slate-300">{s.explanation}</p>
            <p className="mt-0.5 font-mono text-[10px] uppercase tracking-wider text-slate-500">
              {s.explanation_source === "llm" ? "explanation reworded by the language model · span found by rules" : "found by rule"}
            </p>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function RedFlagSummary({ report }: { report: RedFlagReport }) {
  return (
    <div className="panel p-4">
      <h3 className="panel-title">Red flags in the message</h3>
      <p className="mt-1 text-sm">
        Level: <span className={`font-semibold ${RISK_STYLE[report.risk_level]}`}>{RISK_LABEL[report.risk_level]}</span>
      </p>
      <p className="mt-1 text-xs text-slate-400">{report.summary}</p>
      {report.spans.length > 0 && <div className="mt-3"><HighlightedMessage report={report} /></div>}
      {report.url_checks.map((u) => <div key={u.input} className="mt-3"><UrlReport analysis={u} /></div>)}
      <p className="mt-3 font-mono text-[10px] uppercase tracking-wider text-slate-500">method: {report.method}</p>
    </div>
  );
}

export function UrlReport({ analysis: a }: { analysis: UrlAnalysis }) {
  return (
    <div className="rounded-lg border border-ink-600 p-3 text-sm">
      <p className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="break-all font-mono text-xs text-slate-300">{a.normalized_url ?? a.input}</span>
        <span className={`font-semibold ${RISK_STYLE[a.risk_level]}`}>{RISK_LABEL[a.risk_level]} risk{a.risk_level === "invalid" ? "" : ` · score ${a.score}`}</span>
      </p>
      {a.domain && (
        <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-xs">
          <dt className="text-slate-500">Host</dt><dd className="break-all font-mono">{a.domain}</dd>
          <dt className="text-slate-500">Registered domain</dt><dd className="break-all font-mono text-white">{a.registered_domain}</dd>
        </dl>
      )}
      {a.indicators.length > 0 && (
        <ul className="mt-2 space-y-1">
          {a.indicators.map((i) => (
            <li key={i.code} className="flex gap-2 text-xs">
              <span className={`w-14 shrink-0 font-mono uppercase ${SEVERITY_STYLE[i.severity]}`}>{i.severity}</span>
              <span className="text-slate-300">{i.message}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-xs text-slate-400">{a.explanation}</p>
    </div>
  );
}
