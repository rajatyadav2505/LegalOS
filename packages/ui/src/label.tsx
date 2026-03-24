import type { HTMLAttributes, ReactNode } from "react";

export function Label({
  className = "",
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { children: ReactNode }) {
  return (
    <span className={["text-sm font-medium text-slate-100", className].filter(Boolean).join(" ")} {...props}>
      {children}
    </span>
  );
}
