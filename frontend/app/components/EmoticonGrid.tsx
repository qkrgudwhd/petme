"use client";
import type { Emotion, EmoticonItem } from "@/lib/api";

type Props = {
  emotions: Emotion[];
  items: Record<string, EmoticonItem>;
  errors: Record<string, string>;
  busy: Set<string>;
  onRegenerate: (key: string) => void;
  onPickIcon?: (key: string) => void;
  iconKey?: string | null;
};

export function EmoticonGrid({ emotions, items, errors, busy, onRegenerate, onPickIcon, iconKey }: Props) {
  const checker = {
    background: "repeating-conic-gradient(#eee 0% 25%, #fff 0% 50%) 50%/12px 12px",
  } as const;
  return (
    <div className="grid grid-cols-4 sm:grid-cols-8 gap-3">
      {emotions.map((e) => {
        const item = items[e.key];
        const err = errors[e.key];
        const isBusy = busy.has(e.key);
        return (
          <div
            key={e.key}
            className="bg-white border rounded-xl p-2 flex flex-col items-center text-center"
          >
            <div
              className={`w-full aspect-square rounded-lg overflow-hidden flex items-center justify-center relative ${
                isBusy && !item ? "btn-working" : ""
              }`}
              style={!isBusy || item ? checker : undefined}
            >
              {item ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={`${item.url}?t=${item.bytes}`} alt={e.label_ko} className="w-full h-full object-contain relative z-10" />
              ) : isBusy ? (
                <div className="text-[11px] text-white font-bold relative z-10 drop-shadow">
                  생성중...
                </div>
              ) : err ? (
                <div className="text-[10px] text-red-500 px-1 break-all">{err.slice(0, 80)}</div>
              ) : (
                <div className="text-xs text-neutral-300">대기</div>
              )}
            </div>
            <div className="text-[11px] font-medium text-neutral-700 mt-1.5 truncate w-full">
              {e.label_ko}
            </div>
            {item && (
              <div className="flex items-center gap-2 mt-0.5">
                <button
                  onClick={() => onRegenerate(e.key)}
                  disabled={isBusy}
                  className="text-[10px] text-pink-600 hover:underline disabled:opacity-40"
                >
                  ↻ 다시
                </button>
                {onPickIcon && (
                  <button
                    onClick={() => onPickIcon(e.key)}
                    disabled={isBusy || iconKey === e.key}
                    className={`text-[10px] hover:underline disabled:opacity-40 ${
                      iconKey === e.key ? "text-amber-600 font-bold" : "text-amber-700"
                    }`}
                    title="키보드 아이콘으로 지정"
                  >
                    {iconKey === e.key ? "⭐ 아이콘" : "⭐ 아이콘으로"}
                  </button>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
