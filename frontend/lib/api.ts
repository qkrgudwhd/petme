// Capacitor/모바일 빌드: 환경변수로 백엔드 URL 지정
// 웹 dev: next.config.js rewrites가 처리하므로 빈 prefix
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";
const u = (p: string) => `${API_BASE}${p}`;

export type Emotion = { key: string; label_ko: string };
export type PetTypeOption = { key: string; label_ko: string; emoji: string; group?: string };

export type UploadResult = {
  session_id: string;
  pet_type?: string;
  auto_detected?: boolean;
  confidence?: number;
  dynamic_labels?: Record<string, string>;
  analyze_pending?: boolean;
  items: {
    person: { preview_url: string; bytes: number };
    pet: { preview_url: string; bytes: number };
  };
};

export type AnalyzeResult = {
  pet_type: string;
  auto_detected: boolean;
  confidence: number;
  dynamic_labels: Record<string, string>;
};

export async function analyzeSession(sessionId: string): Promise<AnalyzeResult> {
  const res = await fetch(u(`/api/upload/${encodeURIComponent(sessionId)}/analyze`), {
    method: "POST",
  });
  if (!res.ok) throw new Error(`분석 실패: ${await res.text()}`);
  return res.json();
}

export type EmoticonItem = {
  key: string;
  label_ko: string;
  url: string;
  bytes: number;
  ms?: number;
};

export type KeyStatus = { configured: boolean; masked: string };

export async function getKeyStatus(): Promise<KeyStatus> {
  const res = await fetch(u("/api/settings/key"));
  if (!res.ok) throw new Error("키 상태 조회 실패");
  return res.json();
}

export async function saveApiKey(apiKey: string): Promise<KeyStatus> {
  const res = await fetch(u("/api/settings/key"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey }),
  });
  if (!res.ok) throw new Error(`저장 실패: ${await res.text()}`);
  return res.json();
}

export async function deleteApiKey(): Promise<void> {
  const res = await fetch(u("/api/settings/key"), { method: "DELETE" });
  if (!res.ok) throw new Error("삭제 실패");
}

export async function verifyApiKey(): Promise<{ ok: boolean; message?: string }> {
  const res = await fetch(u("/api/settings/key/verify"), { method: "POST" });
  if (res.ok) return { ok: true };
  let msg = "";
  try {
    msg = (await res.json()).detail ?? "";
  } catch {
    msg = await res.text();
  }
  return { ok: false, message: msg };
}

export async function uploadImages(person: File, pet: File, petType = "auto"): Promise<UploadResult> {
  const fd = new FormData();
  fd.append("person", person);
  fd.append("pet", pet);
  fd.append("pet_type", petType);
  const res = await fetch(u("/api/upload"), { method: "POST", body: fd });
  if (!res.ok) throw new Error(`업로드 실패: ${res.status} ${await res.text()}`);
  return res.json();
}

export async function updatePetType(sessionId: string, petType: string): Promise<{ pet_type: string }> {
  const fd = new FormData();
  fd.append("pet_type", petType);
  const res = await fetch(u(`/api/upload/${encodeURIComponent(sessionId)}/pet-type`), {
    method: "POST",
    body: fd,
  });
  if (!res.ok) throw new Error(`종 변경 실패: ${await res.text()}`);
  return res.json();
}

export async function getUploadSession(sessionId: string): Promise<UploadResult> {
  const res = await fetch(u(`/api/upload/${encodeURIComponent(sessionId)}`));
  if (!res.ok) throw new Error(`세션 조회 실패: ${res.status}`);
  return res.json();
}

export async function listEmotions(petType = "dog"): Promise<Emotion[]> {
  const res = await fetch(u(`/api/emotions?pet_type=${encodeURIComponent(petType)}`));
  if (!res.ok) throw new Error("감정 목록 로드 실패");
  return res.json();
}

export async function listPetTypes(): Promise<PetTypeOption[]> {
  const res = await fetch(u("/api/emotions/pet-types"));
  if (!res.ok) throw new Error("종 목록 로드 실패");
  return res.json();
}

export async function regenerate(sessionId: string, emotionKey: string, style: string): Promise<EmoticonItem> {
  const res = await fetch(u("/api/generate/regenerate"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, emotion_key: emotionKey, style }),
  });
  if (!res.ok) throw new Error(`재생성 실패: ${await res.text()}`);
  return res.json();
}

export type IconInfo = {
  source_key: string;
  url: string;
  bytes: number;
  size: number;
};

export type BatchEvent =
  | { type: "start"; data: { total: number; style: string; concurrency: number; person_palette: string[]; pet_palette: string[] } }
  | { type: "item_start"; data: { key: string; label_ko: string } }
  | { type: "item"; data: EmoticonItem }
  | { type: "progress"; data: { done: number; total: number; percent: number } }
  | { type: "error"; data: { key: string; message: string } }
  | { type: "icon"; data: IconInfo }
  | { type: "done"; data: { zip_url: string; icon: IconInfo | null } };

export type UsageInfo = {
  date: string;
  month: string;
  daily_used: number;
  daily_free_limit: number;
  daily_remaining_free: number;
  monthly_spent_krw: number;
  monthly_approved_cap_krw: number;
  monthly_remaining_krw: number;
  krw_per_image: number;
  free_tier_hard_limit: number;
};

export async function getUsage(): Promise<UsageInfo> {
  const res = await fetch(u("/api/generate/usage"));
  if (!res.ok) throw new Error("사용량 조회 실패");
  return res.json();
}

export async function approvePaid(krw: number): Promise<{approved_cap_krw: number; spent_krw: number}> {
  const res = await fetch(u("/api/generate/approve-paid"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ krw }),
  });
  if (!res.ok) throw new Error(`결제 동의 실패: ${await res.text()}`);
  return res.json();
}

export async function revokePaid(): Promise<{approved_cap_krw: number; spent_krw: number}> {
  const res = await fetch(u("/api/generate/revoke-paid"), { method: "POST" });
  if (!res.ok) throw new Error("결제 동의 회수 실패");
  return res.json();
}

export async function setIcon(sessionId: string, sourceKey: string): Promise<IconInfo> {
  const res = await fetch(u("/api/generate/icon"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, source_key: sourceKey }),
  });
  if (!res.ok) throw new Error(`아이콘 설정 실패: ${await res.text()}`);
  return res.json();
}

export function streamBatch(
  sessionId: string,
  style: string,
  onEvent: (e: BatchEvent) => void,
): () => void {
  const url = u(`/api/generate/batch?session_id=${encodeURIComponent(sessionId)}&style=${encodeURIComponent(style)}`);
  const es = new EventSource(url);
  const wrap = (type: BatchEvent["type"]) => (ev: MessageEvent) => {
    try {
      onEvent({ type, data: JSON.parse(ev.data) } as BatchEvent);
    } catch {}
    if (type === "done") es.close();
  };
  es.addEventListener("start", wrap("start") as EventListener);
  es.addEventListener("item_start", wrap("item_start") as EventListener);
  es.addEventListener("item", wrap("item") as EventListener);
  es.addEventListener("icon", wrap("icon") as EventListener);
  es.addEventListener("progress", wrap("progress") as EventListener);
  es.addEventListener("error", wrap("error") as EventListener);
  es.addEventListener("done", wrap("done") as EventListener);
  es.onerror = () => es.close();
  return () => es.close();
}
