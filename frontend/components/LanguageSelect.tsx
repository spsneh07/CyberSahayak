"use client";

import { useEffect, useState } from "react";
import type { Language } from "@/lib/types";

export const LANGUAGES: { id: Language; label: string }[] = [
  { id: "en", label: "English" },
  { id: "hi", label: "हिन्दी (Hindi)" },
];

const KEY = "cybersahayak.language";

/** Selected reply language, remembered in this browser only. */
export function useLanguage(): [Language, (l: Language) => void] {
  const [lang, setLang] = useState<Language>("en");
  useEffect(() => {
    try {
      const saved = localStorage.getItem(KEY);
      if (saved && LANGUAGES.some((l) => l.id === saved)) setLang(saved as Language);
    } catch {
      /* storage unavailable */
    }
  }, []);
  const update = (l: Language) => {
    setLang(l);
    try {
      localStorage.setItem(KEY, l);
    } catch {
      /* storage unavailable */
    }
  };
  return [lang, update];
}

export function LanguageSelect({ value, onChange }: { value: Language; onChange: (l: Language) => void }) {
  return (
    <label className="flex items-center gap-1.5 text-xs text-slate-400">
      Reply language
      <select value={value} onChange={(e) => onChange(e.target.value as Language)}
        className="rounded-md border border-ink-600 bg-ink-950 px-1.5 py-1 text-xs text-white focus:border-signal focus:outline-none">
        {LANGUAGES.map((l) => <option key={l.id} value={l.id}>{l.label}</option>)}
      </select>
    </label>
  );
}
