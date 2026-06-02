"use client";
import { useEffect, useState } from "react";
import { UploadCard } from "./components/UploadCard";
import { EmoticonGrid } from "./components/EmoticonGrid";
import { ApiKeyGate } from "./components/ApiKeyGate";
import { ApiKeyModal } from "./components/ApiKeyModal";
import { PaidConfirmModal } from "./components/PaidConfirmModal";
import { ProgressDashboard, type ActivityEvent } from "./components/ProgressDashboard";
import {
  analyzeSession,
  getUploadSession,
  getUsage,
  listEmotions,
  listPetTypes,
  regenerate,
  setIcon,
  streamBatch,
  updatePetType,
  uploadImages,
  type Emotion,
  type EmoticonItem,
  type IconInfo,
  type KeyStatus,
  type PetTypeOption,
  type UploadResult,
  type UsageInfo,
} from "@/lib/api";

const STYLES = [
  { key: "cartoon2d",  label: "💢 2D 카툰",   hint: "굵은 검은선 + 평면 색 (스티커풍 치비)" },
  { key: "watercolor", label: "🖌 수채화",     hint: "종이 질감 + 번지는 물감, 부드러움" },
  { key: "pastel",     label: "🖍 파스텔",     hint: "분필 가루 질감, 흐릿한 색감" },
  { key: "webtoon",    label: "📖 웹툰",       hint: "가는 펜선 + 큰 눈, 현실 비율" },
  { key: "pixel",      label: "🎮 픽셀아트",   hint: "16-bit 도트 그리드, 레트로 게임" },
  { key: "popart",     label: "🎭 팝아트",     hint: "하프톤 점무늬 + 4색, 만화책풍" },
];

export default function Page() {
  const [keyStatus, setKeyStatus] = useState<KeyStatus | null>(null);
  return (
    <ApiKeyGate onReady={setKeyStatus}>
      <MainApp keyStatus={keyStatus} setKeyStatus={setKeyStatus} />
    </ApiKeyGate>
  );
}

function MainApp({
  keyStatus,
  setKeyStatus,
}: {
  keyStatus: KeyStatus | null;
  setKeyStatus: (s: KeyStatus | null) => void;
}) {
  const [person, setPerson] = useState<File | null>(null);
  const [pet, setPet] = useState<File | null>(null);
  const [style, setStyle] = useState("cartoon2d");
  const [petType, setPetType] = useState("dog");
  const [petTypeOptions, setPetTypeOptions] = useState<PetTypeOption[]>([]);
  const [petTypeAutoDetected, setPetTypeAutoDetected] = useState(false);
  const [petTypeConfidence, setPetTypeConfidence] = useState(0);
  const [dynamicLabels, setDynamicLabels] = useState<Record<string, string>>({});
  const [analyzing, setAnalyzing] = useState(false);
  const [emotions, setEmotions] = useState<Emotion[]>([]);

  const [uploading, setUploading] = useState(false);
  const [upload, setUpload] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [billingError, setBillingError] = useState<boolean>(false);
  const [usage, setUsage] = useState<UsageInfo | null>(null);
  const [paidModalOpen, setPaidModalOpen] = useState(false);
  const refreshUsage = () => getUsage().then(setUsage).catch(() => {});

  const [items, setItems] = useState<Record<string, EmoticonItem>>({});
  const [errs, setErrs] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<Set<string>>(new Set());
  // item_start ~ item/error 사이에 머무는 "지금 처리 중" 키 집합 (최대 CONCURRENCY개)
  const [inFlight, setInFlight] = useState<Set<string>>(new Set());
  const [zipUrl, setZipUrl] = useState<string | null>(null);
  const [icon, setIconInfo] = useState<IconInfo | null>(null);
  const [palettes, setPalettes] = useState<{ person: string[]; pet: string[] } | null>(null);
  const [generating, setGenerating] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // 실시간 활동 로그
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  // 화면에 표시할 감정 목록 — 동적 라벨이 있으면 그걸로 치환
  const displayEmotions = emotions.map((e) =>
    dynamicLabels[e.key] ? { ...e, label_ko: dynamicLabels[e.key] } : e,
  );
  const total = emotions.length || 32;
  const doneCount = Object.keys(items).length;
  const errorCount = Object.keys(errs).length;

  function pushEvent(ev: Omit<ActivityEvent, "t">) {
    setEvents((arr) => [...arr, { ...ev, t: Date.now() }]);
  }

  const [syncedFromLauncher, setSyncedFromLauncher] = useState(false);

  useEffect(() => {
    listPetTypes().then(setPetTypeOptions).catch(() => {});

    const sid = new URLSearchParams(window.location.search).get("session");
    if (sid) {
      getUploadSession(sid)
        .then((r) => {
          setUpload(r);
          if (r.pet_type) setPetType(r.pet_type);
          if (r.dynamic_labels) setDynamicLabels(r.dynamic_labels);
          setSyncedFromLauncher(true);
          pushEvent({ kind: "info", text: `런처에서 업로드된 사진 자동 동기화 완료 (세션 ${sid})` });
          window.history.replaceState({}, "", "/");
        })
        .catch((e) => setError(`세션 복구 실패: ${e}`));
    }
  }, []);

  // 종 선택 바뀔 때마다 라벨 갱신
  useEffect(() => {
    listEmotions(petType).then(setEmotions).catch((e) => setError(String(e)));
  }, [petType]);

  // 사용량 30초마다 갱신 (생성 중에는 10초마다)
  useEffect(() => {
    let alive = true;
    const tick = () => {
      getUsage().then((u) => { if (alive) setUsage(u); }).catch(() => {});
    };
    tick();
    const id = setInterval(tick, generating ? 10000 : 30000);
    return () => { alive = false; clearInterval(id); };
  }, [generating]);

  async function onUpload() {
    if (!person || !pet) {
      setError("인물 사진과 반려동물 사진을 모두 올려주세요.");
      return;
    }
    setError(null);
    setUploading(true);
    setItems({});
    setErrs({});
    setZipUrl(null);
    setEvents([]);
    setStartedAt(null);
    try {
      // 1단계: 빠른 업로드 (누끼/리사이즈만, ~3초)
      const r = await uploadImages(person, pet, "auto");
      setUpload(r);
      pushEvent({ kind: "info", text: `사진 업로드 & 누끼 완료 (세션 ${r.session_id})` });

      // 2단계: 별도 호출로 AI 분석 (~5~10초)
      if (r.analyze_pending) {
        setAnalyzing(true);
        try {
          const a = await analyzeSession(r.session_id);
          setPetType(a.pet_type);
          setPetTypeAutoDetected(a.auto_detected);
          setPetTypeConfidence(a.confidence);
          const found = petTypeOptions.find((p) => p.key === a.pet_type);
          pushEvent({
            kind: "info",
            text: `🔍 자동 감지: ${found?.emoji ?? ""} ${found?.label_ko ?? a.pet_type} (확신도 ${Math.round(a.confidence * 100)}%)`,
          });
          if (a.dynamic_labels && Object.keys(a.dynamic_labels).length > 0) {
            setDynamicLabels(a.dynamic_labels);
            const sample = Object.values(a.dynamic_labels).slice(0, 4).join(", ");
            pushEvent({
              kind: "info",
              text: `✨ 피사체 맞춤 라벨 ${Object.keys(a.dynamic_labels).length}종 생성됨 — 예: ${sample}...`,
            });
          }
        } catch (e) {
          pushEvent({ kind: "error", text: `AI 분석 실패 (기본값으로 진행): ${e}` });
        } finally {
          setAnalyzing(false);
        }
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setUploading(false);
    }
  }

  function startBatch() {
    if (!upload) return;
    setGenerating(true);
    setItems({});
    setErrs({});
    setZipUrl(null);
    setIconInfo(null);
    setPalettes(null);
    setEvents([]);
    setBillingError(false);
    const t0 = Date.now();
    setStartedAt(t0);
    const busySet = new Set<string>(emotions.map((e) => e.key));
    setBusy(busySet);
    setInFlight(new Set());

    const labelOf = (k: string) => emotions.find((e) => e.key === k)?.label_ko ?? k;
    pushEvent({ kind: "info", text: `32종 일괄 생성 시작 — 스타일: ${style}` });

    streamBatch(upload.session_id, style, (ev) => {
      if (ev.type === "item_start") {
        setInFlight((s) => new Set(s).add(ev.data.key));
        const lab = emotions.find((e) => e.key === ev.data.key)?.label_ko ?? ev.data.key;
        pushEvent({ kind: "info", text: `처리 중: ${lab}`, key: ev.data.key });
      } else if (ev.type === "item") {
        setItems((m) => ({ ...m, [ev.data.key]: ev.data }));
        setBusy((s) => {
          const n = new Set(s);
          n.delete(ev.data.key);
          return n;
        });
        setInFlight((s) => {
          const n = new Set(s);
          n.delete(ev.data.key);
          return n;
        });
        pushEvent({
          kind: "item",
          key: ev.data.key,
          ms: ev.data.ms,
          bytes: ev.data.bytes,
          text: `${labelOf(ev.data.key)}  (${((ev.data.ms ?? 0) / 1000).toFixed(1)}초, ${Math.round(
            ev.data.bytes / 1024,
          )}KB)`,
        });
      } else if (ev.type === "error") {
        setErrs((m) => ({ ...m, [ev.data.key]: ev.data.message }));
        setBusy((s) => {
          const n = new Set(s);
          n.delete(ev.data.key);
          return n;
        });
        setInFlight((s) => {
          const n = new Set(s);
          n.delete(ev.data.key);
          return n;
        });
        // 결제 한도 에러는 한 번이라도 발생하면 배너로 알림
        const msg = ev.data.message.toLowerCase();
        if (msg.includes("need_paid_confirm")) {
          // 무료 한도 초과 → 결제 동의 모달
          setPaidModalOpen(true);
          refreshUsage();
        } else if (msg.includes("billing_limit") || msg.includes("spending cap") ||
                   msg.includes("monthly spending") || msg.includes("budget exceeded")) {
          setBillingError(true);
        }
        pushEvent({
          kind: "error",
          key: ev.data.key,
          text: `${labelOf(ev.data.key)} 실패 — ${ev.data.message.slice(0, 120)}`,
        });
      } else if (ev.type === "icon") {
        setIconInfo(ev.data);
        pushEvent({
          kind: "info",
          text: `🎨 키보드 아이콘 생성됨 (78x78, ${Math.round(ev.data.bytes / 1024)}KB, 소스: ${ev.data.source_key})`,
        });
      } else if (ev.type === "done") {
        setZipUrl(ev.data.zip_url);
        if (ev.data.icon) setIconInfo(ev.data.icon);
        setGenerating(false);
        const total_s = ((Date.now() - t0) / 1000).toFixed(1);
        pushEvent({ kind: "done", text: `전체 완료! (총 ${total_s}초) — ZIP 준비됨` });
      } else if (ev.type === "start") {
        setPalettes({ person: ev.data.person_palette, pet: ev.data.pet_palette });
        pushEvent({
          kind: "info",
          text: `백엔드 작업 시작 (동시성 ${ev.data.concurrency}, 색상 ${ev.data.person_palette.length + ev.data.pet_palette.length}개 추출)`,
        });
      }
    });
  }

  async function onPickIcon(key: string) {
    if (!upload) return;
    try {
      const info = await setIcon(upload.session_id, key);
      setIconInfo(info);
      pushEvent({
        kind: "info",
        text: `🎨 아이콘 변경: ${emotions.find((e) => e.key === key)?.label_ko ?? key} (${Math.round(info.bytes / 1024)}KB)`,
      });
    } catch (e) {
      setError(String(e));
    }
  }

  async function onRegenerate(key: string) {
    if (!upload) return;
    setBusy((s) => new Set(s).add(key));
    setErrs((m) => {
      const n = { ...m };
      delete n[key];
      return n;
    });
    const labelOf = emotions.find((e) => e.key === key)?.label_ko ?? key;
    pushEvent({ kind: "info", text: `재생성 요청: ${labelOf}` });
    try {
      const item = await regenerate(upload.session_id, key, style);
      setItems((m) => ({ ...m, [key]: item }));
      pushEvent({
        kind: "item",
        key,
        ms: item.ms,
        bytes: item.bytes,
        text: `${labelOf} 재생성 완료 (${Math.round(item.bytes / 1024)}KB)`,
      });
    } catch (e) {
      setErrs((m) => ({ ...m, [key]: String(e) }));
      pushEvent({ kind: "error", key, text: `${labelOf} 재생성 실패` });
    } finally {
      setBusy((s) => {
        const n = new Set(s);
        n.delete(key);
        return n;
      });
    }
  }

  const showProgress = startedAt !== null || generating || doneCount > 0;

  return (
    <main className="max-w-6xl mx-auto px-6 py-10">
      <header className="mb-8 flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">🐾 PetMe-Moji</h1>
          <p className="text-neutral-500 mt-1">
            인물 + 반려동물 사진으로 카카오톡 이모티콘 32종을 자동 생성해드려요.
          </p>
        </div>
        <button
          onClick={() => setSettingsOpen(true)}
          className="px-3 py-2 rounded-lg border text-sm font-medium bg-white border-neutral-300 hover:border-pink-400"
          title="API 키 설정"
        >
          ⚙ {keyStatus?.masked || "키 설정"}
        </button>
      </header>

      <ApiKeyModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onChanged={setKeyStatus}
      />

      {/* 무료 티어 + 월간 결제 사용량 배너 */}
      <section className="mb-6 bg-gradient-to-r from-emerald-50 to-amber-50 border border-emerald-200 rounded-2xl p-4">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-3 flex-1 min-w-[260px]">
            <div className="text-2xl">🆓</div>
            <div className="flex-1">
              <div className="text-sm font-bold text-emerald-900">
                무료 티어 우선 + 결제 게이트
              </div>
              <div className="text-xs text-emerald-700 mt-0.5">
                일 95장까지 무료. 초과 시 결제 동의 모달이 뜹니다. 동의 안 하면 자동 정지.
              </div>
            </div>
          </div>
          {usage && (
            <div className="flex gap-4">
              <div className="text-right">
                <div className="text-[10px] text-emerald-700">오늘 무료</div>
                <div className="font-bold text-emerald-900 tabular-nums text-sm">
                  {usage.daily_used} / {usage.daily_free_limit}장
                </div>
                <div className="w-28 h-1.5 bg-white rounded-full mt-0.5 overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      usage.daily_used >= usage.daily_free_limit ? "bg-red-500" : "bg-emerald-500"
                    }`}
                    style={{ width: `${Math.min(100, (usage.daily_used / usage.daily_free_limit) * 100)}%` }}
                  />
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-amber-700">이번 달 결제</div>
                <div className="font-bold text-amber-900 tabular-nums text-sm">
                  ₩{usage.monthly_spent_krw.toLocaleString()} / ₩{usage.monthly_approved_cap_krw.toLocaleString()}
                </div>
                <div className="w-28 h-1.5 bg-white rounded-full mt-0.5 overflow-hidden">
                  <div
                    className="h-full bg-amber-500 transition-all"
                    style={{ width: usage.monthly_approved_cap_krw > 0
                      ? `${Math.min(100, (usage.monthly_spent_krw / usage.monthly_approved_cap_krw) * 100)}%`
                      : "0%" }}
                  />
                </div>
                <button
                  onClick={() => setPaidModalOpen(true)}
                  className="text-[10px] text-pink-600 hover:underline mt-0.5"
                >
                  결제 한도 관리 →
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      <PaidConfirmModal
        open={paidModalOpen}
        usage={usage}
        onClose={() => { setPaidModalOpen(false); refreshUsage(); }}
        onApproved={() => { setPaidModalOpen(false); refreshUsage(); }}
      />

      <section className="mb-4">
        <div className="text-sm font-semibold mb-2 flex items-center gap-2">
          이미지 종류
          {!upload && (
            <span className="text-[10px] font-normal text-neutral-400">
              (사진 업로드하면 자동 인식)
            </span>
          )}
          {analyzing && (
            <span className="px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 text-[10px] font-bold animate-pulse">
              🤖 AI가 사진을 분석 중...
            </span>
          )}
          {!analyzing && upload && petTypeAutoDetected && (
            <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-bold">
              🔍 사진에서 자동 인식됨 ({Math.round(petTypeConfidence * 100)}%)
            </span>
          )}
          {!analyzing && upload && !petTypeAutoDetected && (
            <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 text-[10px] font-bold">
              ✏ 수동 설정됨
            </span>
          )}
        </div>

        {(["동물", "기타"] as const).map((group) => {
          const items = petTypeOptions.filter((p) => p.group === group);
          if (items.length === 0) return null;
          return (
            <div key={group} className="mb-2">
              <div className="text-[10px] text-neutral-400 mb-1 font-medium">{group}</div>
              <div className="flex flex-wrap gap-2">
                {items.map((p) => (
                  <button
                    key={p.key}
                    onClick={async () => {
                      setPetType(p.key);
                      setPetTypeAutoDetected(false);
                      if (upload) {
                        try {
                          await updatePetType(upload.session_id, p.key);
                          pushEvent({ kind: "info", text: `종 수동 변경: ${p.emoji} ${p.label_ko}` });
                        } catch (e) {
                          setError(String(e));
                        }
                      }
                    }}
                    className={`px-3 py-1.5 rounded-full text-sm border transition flex items-center gap-1.5 ${
                      petType === p.key
                        ? "bg-amber-400 text-white border-amber-400"
                        : "bg-white text-neutral-700 border-neutral-300 hover:border-amber-300"
                    }`}
                  >
                    <span>{p.emoji}</span>
                    <span>{p.label_ko}</span>
                  </button>
                ))}
              </div>
            </div>
          );
        })}

        <div className="text-[11px] text-neutral-500 mt-1">
          동물은 종에 맞는 소리·행동(멍멍/야옹/짹짹/꾹꾹이…)으로,
          식물·인형·사물·음식은 의인화된 표현(쑥쑥/꼬옥/띠리링/냠냠…)으로 생성됩니다.
          잘못 인식된 경우 다른 칩을 눌러 수동 변경하세요.
        </div>
      </section>

      <section className="grid md:grid-cols-2 gap-4 mb-6">
        <UploadCard label="① 인물 사진" onChange={setPerson} />
        <UploadCard label="② 함께할 이미지 (반려동물·식물·인형·사물 등)" onChange={setPet} />
      </section>

      <section className="mb-4">
        <div className="text-sm font-semibold mb-2">화풍 선택</div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {STYLES.map((s) => (
            <button
              key={s.key}
              onClick={() => setStyle(s.key)}
              className={`px-3 py-2.5 rounded-xl text-sm border transition text-left ${
                style === s.key
                  ? "bg-pink-500 text-white border-pink-500"
                  : "bg-white text-neutral-700 border-neutral-300 hover:border-pink-300"
              }`}
            >
              <div className="font-semibold">{s.label}</div>
              <div className={`text-[10px] mt-0.5 ${style === s.key ? "text-pink-100" : "text-neutral-500"}`}>
                {s.hint}
              </div>
            </button>
          ))}
        </div>
      </section>

      <div className="grid sm:grid-cols-2 gap-3 mb-8">
        <button
          onClick={onUpload}
          disabled={uploading}
          className={`py-3 rounded-2xl border font-semibold transition ${
            uploading
              ? "btn-working-blue"
              : "bg-white hover:border-pink-400 disabled:opacity-50"
          }`}
        >
          {uploading ? "🔄 사진 업로드 & 누끼 처리 중..." : upload ? "↻ 사진 다시 업로드" : "1) 사진 업로드 & 누끼"}
        </button>
        <button
          onClick={startBatch}
          disabled={!upload || generating || analyzing}
          className={`py-3 rounded-2xl font-semibold transition ${
            generating
              ? "btn-working"
              : "bg-pink-500 text-white hover:bg-pink-600 disabled:opacity-40"
          }`}
        >
          {generating ? "✨ 32종 이모티콘 생성 중..." : analyzing ? "AI 분석 대기 중..." : "2) 32종 이모티콘 생성 시작"}
        </button>
      </div>

      {error && <div className="mb-4 text-red-600 text-sm whitespace-pre-wrap">{error}</div>}

      {billingError && (
        <div className="mb-4 bg-red-50 border-2 border-red-300 rounded-2xl p-4">
          <div className="flex items-start gap-3">
            <div className="text-3xl">💳</div>
            <div className="flex-1">
              <h3 className="font-bold text-red-900 mb-1">
                Google Cloud 결제 한도 도달 (Spending Cap Reached)
              </h3>
              <p className="text-sm text-red-800 mb-3">
                현재 API 키가 속한 Google Cloud 프로젝트의 <b>월별 지출 한도</b>에 도달했습니다.
                재시도해도 같은 오류가 계속 발생합니다. 다음 중 하나를 조치하세요:
              </p>
              <div className="space-y-2 text-sm">
                <div className="bg-white rounded-lg p-3 border border-red-200">
                  <b className="text-red-900">방법 1 — 한도 늘리기/제거 (가장 간단)</b>
                  <ol className="list-decimal list-inside text-red-800 mt-1.5 space-y-0.5 text-xs">
                    <li>
                      <a
                        href="https://console.cloud.google.com/billing"
                        target="_blank"
                        rel="noreferrer"
                        className="text-pink-600 underline font-semibold"
                      >
                        Google Cloud Console 결제 페이지
                      </a>{" "}
                      접속
                    </li>
                    <li>본인 프로젝트 → <b>예산 및 알림(Budgets & alerts)</b></li>
                    <li>설정된 예산 클릭 → 금액 증액 또는 [삭제]</li>
                  </ol>
                </div>
                <div className="bg-white rounded-lg p-3 border border-red-200">
                  <b className="text-red-900">방법 2 — 새 API 키 발급 (다른 프로젝트로)</b>
                  <ol className="list-decimal list-inside text-red-800 mt-1.5 space-y-0.5 text-xs">
                    <li>
                      <a
                        href="https://aistudio.google.com/apikey"
                        target="_blank"
                        rel="noreferrer"
                        className="text-pink-600 underline font-semibold"
                      >
                        AI Studio
                      </a>{" "}
                      → <b>+ Create API key in new project</b>
                    </li>
                    <li>키 복사</li>
                    <li>화면 우측 상단 <b>⚙</b> → 새 키 입력 + 저장</li>
                    <li>이 화면에서 [생성 시작] 다시 클릭</li>
                  </ol>
                </div>
                <div className="bg-white rounded-lg p-3 border border-red-200">
                  <b className="text-red-900">방법 3 — 다음 달까지 기다리기</b>
                  <p className="text-red-800 text-xs mt-1">월별 한도는 매월 1일 리셋됩니다.</p>
                </div>
              </div>
              <button
                onClick={() => setBillingError(false)}
                className="mt-3 text-xs text-red-700 underline hover:no-underline"
              >
                이 안내 닫기
              </button>
            </div>
          </div>
        </div>
      )}

      {upload && (
        <section className="mb-6">
          <h2 className="font-semibold mb-3 text-sm flex items-center gap-2">
            누끼 미리보기 (세션 {upload.session_id})
            {syncedFromLauncher && (
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-bold">
                ✓ 런처에서 자동 동기화됨
              </span>
            )}
          </h2>
          <div className="grid grid-cols-2 gap-4 max-w-md">
            {(["person", "pet"] as const).map((k) => (
              <div key={k} className="bg-white rounded-xl border p-3 text-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={upload.items[k].preview_url}
                  alt={k}
                  className="mx-auto"
                  style={{
                    width: 140,
                    height: 140,
                    background:
                      "repeating-conic-gradient(#eee 0% 25%, #fff 0% 50%) 50%/14px 14px",
                  }}
                />
                <div className="text-[11px] text-neutral-500 mt-2">
                  {k} · {Math.round(upload.items[k].bytes / 1024)}KB
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {showProgress && (
        <section className="mb-8">
          <ProgressDashboard
            total={total}
            done={doneCount}
            errors={errorCount}
            startedAt={startedAt}
            events={events}
            zipUrl={zipUrl}
            currentlyProcessing={Array.from(inFlight)
              .map((k) => emotions.find((e) => e.key === k)?.label_ko ?? k)}
          />
        </section>
      )}

      {palettes && (palettes.person.length > 0 || palettes.pet.length > 0) && (
        <section className="mb-4 bg-slate-50 border border-slate-200 rounded-2xl p-4">
          <div className="text-xs font-semibold text-slate-700 mb-2">
            🎨 원본에서 추출된 시그니처 색상 (32장 모두에 적용)
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            {([
              ["인물", palettes.person],
              ["반려동물", palettes.pet],
            ] as const).map(([who, colors]) => (
              <div key={who} className="flex items-center gap-2">
                <span className="text-xs text-slate-600 w-16 shrink-0">{who}</span>
                <div className="flex flex-wrap gap-1.5">
                  {colors.map((c) => (
                    <div key={c} className="flex items-center gap-1">
                      <span
                        className="w-5 h-5 rounded border border-slate-300"
                        style={{ background: c }}
                        title={c}
                      />
                      <code className="text-[10px] text-slate-500">{c}</code>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {icon && (
        <section className="mb-6 bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-center gap-4">
          <div
            className="rounded-lg overflow-hidden"
            style={{
              width: 78, height: 78,
              background: "repeating-conic-gradient(#eee 0% 25%, #fff 0% 50%) 50%/10px 10px",
            }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={`${icon.url}?t=${icon.bytes}`} alt="키보드 아이콘" width={78} height={78} />
          </div>
          <div className="flex-1 text-sm">
            <div className="font-bold text-amber-900 mb-0.5">키보드 메인 아이콘 (78×78)</div>
            <div className="text-xs text-amber-800">
              소스: <code className="bg-white px-1.5 py-0.5 rounded">
                {emotions.find((e) => e.key === icon.source_key)?.label_ko ?? icon.source_key}
              </code>
              {" · "}{Math.round(icon.bytes / 1024)}KB / 16KB
              {" · "}<a href={icon.url} download="icon.png" className="text-amber-700 underline">개별 다운로드</a>
            </div>
            <div className="text-[11px] text-amber-700 mt-1">
              아래 32종 중 어느 칸에서든 [⭐ 아이콘으로] 클릭하면 변경됩니다.
            </div>
          </div>
        </section>
      )}

      <section className="mt-4">
        {Object.keys(dynamicLabels).length > 0 && (
          <div className="mb-3 px-3 py-2 rounded-lg bg-violet-50 border border-violet-200 text-xs text-violet-700">
            ✨ 이 32종 라벨은 업로드된 이미지를 보고 <b>자동 맞춤 생성</b>된 것입니다.
            (기본값과 달리 피사체의 특징이 반영됨)
          </div>
        )}
        <EmoticonGrid
          emotions={displayEmotions}
          items={items}
          errors={errs}
          busy={busy}
          onRegenerate={onRegenerate}
          onPickIcon={onPickIcon}
          iconKey={icon?.source_key ?? null}
        />
      </section>
    </main>
  );
}
