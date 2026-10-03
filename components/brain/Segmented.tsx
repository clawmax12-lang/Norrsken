"use client";

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
  hint?: string;
  disabled?: boolean;
}

/** Rounded segmented pill (PRD §12.3/§12.6) exposed as a radio group. */
export function Segmented<T extends string>({ label, value, options, onChange }: { label: string; value: T; options: SegmentOption<T>[]; onChange: (value: T) => void }) {
  return (
    <div className="bv-seg" role="radiogroup" aria-label={label}>
      <span className="bv-seg-label">{label}</span>
      <div className="bv-seg-track">
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={o.value === value}
            className={o.value === value ? "bv-seg-active" : undefined}
            disabled={o.disabled}
            title={o.hint}
            onClick={() => onChange(o.value)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
