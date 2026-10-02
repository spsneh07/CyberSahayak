import { Suspense } from "react";
import { AssistantView } from "@/components/AssistantView";

export default function AssistantPage() {
  return (
    <Suspense fallback={<p className="p-8 text-slate-400">Loading assistant…</p>}>
      <AssistantView />
    </Suspense>
  );
}
