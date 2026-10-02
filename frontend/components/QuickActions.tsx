import type { Intent } from "@/lib/types";

export interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: string;
  /** Explicit action sent to the backend; undefined lets the backend detect intent. */
  action?: Intent;
  /** Text placed in the composer (user edits it before sending). */
  prefill?: string;
  /** Send immediately with this text. */
  autoSend?: string;
}

export const QUICK_ACTIONS: QuickAction[] = [
  { id: "report", title: "Report Incident", icon: "⚠", description: "Describe what happened and get a full analysis.",
    action: "report_incident", prefill: "" },
  { id: "understand", title: "Understand Scam", icon: "?", description: "Ask how a type of scam works.",
    action: "question", prefill: "How does a UPI collect request scam work?" },
  { id: "check", title: "Check Suspicious Message", icon: "⌕", description: "Paste a message, call script or link to check it.",
    action: "check_message", prefill: "Is this a scam? \"" },
  { id: "complaint", title: "Generate Complaint", icon: "✎", description: "Draft an editable formal complaint.",
    action: "generate_complaint", autoSend: "Please draft a formal complaint for my incident." },
  { id: "evidence", title: "Evidence Checklist", icon: "☑", description: "What to save before it's lost.",
    action: "evidence_checklist", autoSend: "What evidence should I preserve?" },
  { id: "tips", title: "Cyber Safety Tips", icon: "✦", description: "Personalised prevention advice.",
    action: "safety_tips", autoSend: "Give me cyber safety tips." },
];

export function QuickActionGrid({ onPick, compact = false, disabled = false }: {
  onPick: (a: QuickAction) => void; compact?: boolean; disabled?: boolean;
}) {
  return (
    <ul className={compact ? "flex flex-wrap gap-2" : "grid gap-3 sm:grid-cols-2 lg:grid-cols-3"} aria-label="Quick actions">
      {QUICK_ACTIONS.map((a) => (
        <li key={a.id}>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onPick(a)}
            className={
              compact
                ? "btn-ghost px-2.5 py-1.5 text-xs"
                : "panel group flex h-full w-full items-start gap-3 p-4 text-left transition hover:border-signal/60 disabled:opacity-50"
            }
          >
            <span aria-hidden className={compact ? "text-signal" : "grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-signal/10 font-mono text-signal ring-1 ring-signal/30"}>
              {a.icon}
            </span>
            {compact ? (
              a.title
            ) : (
              <span>
                <span className="block font-medium text-white group-hover:text-signal">{a.title}</span>
                <span className="mt-0.5 block text-sm text-slate-400">{a.description}</span>
              </span>
            )}
          </button>
        </li>
      ))}
    </ul>
  );
}
