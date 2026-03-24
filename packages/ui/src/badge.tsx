import type { HTMLAttributes, ReactNode } from "react";

type BadgeVariant = "neutral" | "info" | "success" | "warning" | "danger";

const badgeStyles: Record<BadgeVariant, string> = {
  neutral: "border-white/10 bg-white/5 text-slate-200",
  info: "border-cyan-500/20 bg-cyan-500/10 text-cyan-100",
  success: "border-emerald-500/20 bg-emerald-500/10 text-emerald-100",
  warning: "border-amber-500/20 bg-amber-500/10 text-amber-100",
  danger: "border-red-500/20 bg-red-500/10 text-red-100"
};

export function Badge({
  className = "",
  variant = "neutral",
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement> & {
  variant?: BadgeVariant;
  children: ReactNode;
}) {
  return (
    <span
      className={[
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.18em]",
        badgeStyles[variant],
        className
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {children}
    </span>
  );
}
