import type { EvidenceFile } from "./types";

/** Files larger than this are not read into memory for hashing. */
export const MAX_HASH_BYTES = 200 * 1024 * 1024;

export class HashError extends Error {}

/** SHA-256 of a file, computed in the browser. The file is never uploaded. */
export async function sha256File(file: File): Promise<string> {
  if (!globalThis.crypto?.subtle) {
    throw new HashError("This browser can't compute fingerprints here (it needs https or localhost).");
  }
  if (file.size > MAX_HASH_BYTES) {
    throw new HashError(`${file.name} is larger than 200 MB; fingerprint it with a desktop tool instead.`);
  }
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
}

export async function fingerprint(file: File): Promise<EvidenceFile> {
  return {
    name: file.name,
    size: file.size,
    media_type: file.type,
    sha256: await sha256File(file),
    recorded_at: new Date().toISOString(),
    last_modified: file.lastModified ? new Date(file.lastModified).toISOString() : null,
    checklist_item: null,
  };
}

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export function downloadJson(filename: string, data: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
