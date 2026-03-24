import type { SelectHTMLAttributes } from "react";

export function Select({
  className = "",
  options,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & {
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <select
      className={[
        "h-11 w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 text-sm text-white",
        "placeholder:text-slate-500 focus:border-saffron-500/50 focus:outline-none focus:ring-2 focus:ring-saffron-500/20",
        className
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
