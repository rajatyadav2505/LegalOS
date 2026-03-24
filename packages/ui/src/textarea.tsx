import type { TextareaHTMLAttributes } from "react";

export function Textarea({ className = "", ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={[
        "min-h-32 w-full rounded-2xl border border-white/10 bg-slate-950/40 px-4 py-3 text-sm text-white",
        "placeholder:text-slate-500 focus:border-saffron-500/50 focus:outline-none focus:ring-2 focus:ring-saffron-500/20",
        className
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    />
  );
}
