import { categoryLabel, pct } from "@/lib/labels";
import type { Classification, FactSource, IncidentData } from "@/lib/types";

const SOURCE_BADGE: Record<FactSource, { label: string; cls: string }> = {
  user_provided: { label: "you said", cls: "text-safe" },
  inferred: { label: "inferred", cls: "text-warn" },
  unknown: { label: "unknown", cls: "text-slate-500" },
};

function Row({ label, value, source }: { label: string; value: string | null; source?: FactSource }) {
  // A present value never gets the "unknown" badge; show no badge if its provenance wasn't recorded.
  const badge = !value ? SOURCE_BADGE.unknown : source && source !== "unknown" ? SOURCE_BADGE[source] : null;
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-ink-700/60 py-1.5 last:border-0">
      <dt className="text-sm text-slate-400">{label}</dt>
      <dd className="text-right text-sm">
        <span className={value ? "text-white" : "italic text-slate-500"}>{value ?? "Not provided"}</span>
        {badge && <span className={`ml-2 font-mono text-[10px] uppercase ${badge.cls}`}>{badge.label}</span>}
      </dd>
    </div>
  );
}

function ConfidenceBar({ value }: { value: number }) {
  const color = value >= 0.7 ? "bg-safe" : value >= 0.4 ? "bg-warn" : "bg-danger";
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-700" role="meter" aria-valuemin={0} aria-valuemax={100}
      aria-valuenow={Math.round(value * 100)} aria-label="Classification confidence">
      <div className={`h-full ${color}`} style={{ width: pct(value) }} />
    </div>
  );
}

export function IncidentSummary({ incident, classification }: { incident: IncidentData; classification: Classification | null }) {
  const fs = incident.field_sources;
  const loss =
    incident.amount != null
      ? `${incident.currency ?? ""} ${incident.amount.toLocaleString("en-IN")}`.trim()
      : incident.financial_loss === true ? "Yes (amount unknown)" : incident.financial_loss === false ? "No" : null;
  const identifiers = [...incident.phone_numbers, ...incident.upi_ids, ...incident.urls, ...incident.emails];

  return (
    <section className="panel p-4" aria-labelledby="summary-title">
      <h2 id="summary-title" className="panel-title">Incident summary</h2>
      {classification && (
        <div className="mt-3">
          <p className="text-lg font-semibold text-white">{categoryLabel(classification.category)}</p>
          {classification.subtype && <p className="text-sm text-slate-400">{classification.subtype}</p>}
          <div className="mt-2 flex items-center gap-3">
            <ConfidenceBar value={classification.confidence} />
            <span className="font-mono text-xs text-slate-300">{pct(classification.confidence)}</span>
          </div>
          {classification.reasoning && <p className="mt-2 text-sm text-slate-300">{classification.reasoning}</p>}
          {classification.alternatives.length > 0 && (
            <p className="mt-2 flex flex-wrap gap-1.5 text-xs text-slate-400">
              Also possible:
              {classification.alternatives.map((a) => (
                <span key={a.category} className="chip">{categoryLabel(a.category)} · {pct(a.confidence)}</span>
              ))}
            </p>
          )}
        </div>
      )}
      <dl className="mt-3">
        <Row label="Platform" value={incident.platform} source={fs.platform} />
        <Row label="Date / time" value={incident.date_time} source={fs.date_time} />
        <Row label="Financial loss" value={loss} source={incident.amount != null ? fs.amount : fs.financial_loss} />
        <Row label="Evidence" value={incident.evidence_available.join(", ") || null} source={fs.evidence_available} />
        <Row label="Suspect identifiers" value={identifiers.join(", ") || null} />
        {incident.account_identifiers.length > 0 && <Row label="Transaction / account IDs" value={incident.account_identifiers.join(", ")} />}
      </dl>
      {incident.missing_information.length > 0 && (
        <p className="mt-3 text-xs text-warn">Still unknown: {incident.missing_information.join(", ").replaceAll("_", " ")}</p>
      )}
    </section>
  );
}
