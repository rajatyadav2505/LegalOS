import type { InputHTMLAttributes } from "react";

export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={[
        "h-11 w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 text-sm text-white",
        "placeholder:text-slate-500 focus:border-saffron-500/50 focus:outline-none focus:ring-2 focus:ring-saffron-500/20",
        className
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    />
  );
}
