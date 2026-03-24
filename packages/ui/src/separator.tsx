import type { HTMLAttributes } from "react";

export function Separator({ className = "", ...props }: HTMLAttributes<HTMLHRElement>) {
  return <hr className={["border-white/10", className].filter(Boolean).join(" ")} {...props} />;
}
