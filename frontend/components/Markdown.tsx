import { Fragment, type ReactNode } from "react";

/** Minimal, safe markdown: paragraphs, bullet/numbered lists, **bold**, _italic_. No raw HTML. */
function inline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|_[^_]+_)/g);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**")) return <strong key={i} className="text-white">{p.slice(2, -2)}</strong>;
    if (p.startsWith("_") && p.endsWith("_") && p.length > 2) return <em key={i} className="text-slate-400">{p.slice(1, -1)}</em>;
    return <Fragment key={i}>{p}</Fragment>;
  });
}

export function Markdown({ text }: { text: string }) {
  const blocks = text.trim().split(/\n{2,}/);
  return (
    <div className="space-y-2 leading-relaxed">
      {blocks.map((block, bi) => {
        const lines = block.split("\n");
        const listItems = lines.filter((l) => /^\s*([-*]|\d+\.)\s+/.test(l));
        if (listItems.length && listItems.length >= lines.length - 1) {
          const header = listItems.length < lines.length ? lines[0] : null;
          const ordered = /^\s*\d+\./.test(listItems[0] ?? "");
          const items = listItems.map((l) => l.replace(/^\s*([-*]|\d+\.)\s+/, ""));
          const List = ordered ? "ol" : "ul";
          return (
            <div key={bi}>
              {header && <p>{inline(header)}</p>}
              <List className={`${ordered ? "list-decimal" : "list-disc"} space-y-1 pl-5 marker:text-signal`}>
                {items.map((it, ii) => <li key={ii}>{inline(it)}</li>)}
              </List>
            </div>
          );
        }
        return <p key={bi}>{lines.map((l, li) => <Fragment key={li}>{li > 0 && <br />}{inline(l)}</Fragment>)}</p>;
      })}
    </div>
  );
}
