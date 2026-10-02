export const CATEGORY_LABELS: Record<string, string> = {
  phishing: "Phishing",
  smishing: "Smishing (SMS phishing)",
  vishing: "Vishing (voice phishing)",
  upi_fraud: "UPI / payment fraud",
  banking_fraud: "Banking fraud",
  otp_scam: "OTP scam",
  shopping_fraud: "Online shopping fraud",
  investment_scam: "Investment scam",
  job_scam: "Job / employment scam",
  identity_theft: "Identity theft",
  account_takeover: "Account takeover",
  social_media_impersonation: "Social-media impersonation",
  fake_website: "Fake website",
  malware: "Malware",
  ransomware: "Ransomware",
  sextortion: "Sextortion",
  cyberbullying: "Cyberbullying / harassment",
  data_theft: "Data theft / breach",
  romance_scam: "Romance scam",
  crypto_scam: "Cryptocurrency scam",
  unknown: "Unknown / Needs more information",
};

export const categoryLabel = (id: string | null | undefined) => (id ? CATEGORY_LABELS[id] ?? id : "Unknown");

export const STAGES: { id: string; label: string }[] = [
  { id: "analyzing", label: "Analyzing" },
  { id: "extracting", label: "Extracting" },
  { id: "classifying", label: "Classifying" },
  { id: "retrieving", label: "Retrieving sources" },
  { id: "generating", label: "Generating" },
  { id: "saving", label: "Saving" },
];

export const pct = (n: number) => `${Math.round(n * 100)}%`;
