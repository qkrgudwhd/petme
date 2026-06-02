"use client";
import { useRef, useState } from "react";

type Props = {
  label: string;
  onChange: (file: File | null) => void;
};

export function UploadCard({ label, onChange }: Props) {
  const [preview, setPreview] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function pick(file: File | null) {
    onChange(file);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(file ? URL.createObjectURL(file) : null);
  }

  return (
    <div
      className="rounded-2xl border-2 border-dashed border-neutral-300 bg-white p-6 hover:border-pink-400 transition cursor-pointer text-center"
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        const f = e.dataTransfer.files?.[0];
        if (f) pick(f);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="hidden"
        onChange={(e) => pick(e.target.files?.[0] ?? null)}
      />
      <div className="text-sm font-semibold text-neutral-700 mb-3">{label}</div>
      {preview ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={preview} alt={label} className="mx-auto max-h-48 rounded-xl" />
      ) : (
        <div className="py-12 text-neutral-400 text-sm">
          클릭하거나 사진을 끌어다 놓으세요
          <div className="text-xs mt-1">JPG / PNG / WEBP · 최대 15MB</div>
        </div>
      )}
    </div>
  );
}
