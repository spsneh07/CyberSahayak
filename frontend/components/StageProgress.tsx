import { STAGES } from "@/lib/labels";

/** Shows the pipeline stages actually reported by the backend (SSE), not timers. */
export function StageProgress({ reached, active }: { reached: string[]; active: boolean }) {
  const current = reached[reached.length - 1];
  return (
    <div className="panel px-4 py-3" role="status" aria-live="polite">
      <ol className="flex flex-wrap items-center gap-x-1 gap-y-2 font-mono text-xs">
        {STAGES.map((s, i) => {
          const done = reached.includes(s.id) && (s.id !== current || !active);
          const isCurrent = active && s.id === current;
          return (
            <li key={s.id} className="flex items-center gap-1">
              <span
                className={
                  isCurrent
                    ? "flex items-center gap-1.5 rounded-md bg-signal/15 px-2 py-1 text-signal"
                    : done
                      ? "flex items-center gap-1.5 rounded-md px-2 py-1 text-safe"
                      : "flex items-center gap-1.5 rounded-md px-2 py-1 text-slate-500"
                }
              >
                <span aria-hidden>{isCurrent ? <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-signal" /> : done ? "✓" : "○"}</span>
                {s.label}
                {isCurrent && <span className="sr-only">(in progress)</span>}
              </span>
              {i < STAGES.length - 1 && <span aria-hidden className="text-ink-600">→</span>}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
