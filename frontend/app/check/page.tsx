import { Suspense } from "react";
import { CheckView } from "@/components/CheckView";

export default function CheckPage() {
  return (
    <Suspense fallback={<p className="p-8 text-slate-400">Loading…</p>}>
      <CheckView />
    </Suspense>
  );
}
