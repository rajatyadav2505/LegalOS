import type { ReactNode } from "react";
import { Label } from "./label.js";

export function Field({
  label,
  children,
  helperText
}: {
  label: string;
  helperText?: string;
  children: ReactNode;
}) {
  return (
    <label className="block space-y-2">
      <Label>{label}</Label>
      {children}
      {helperText ? <p className="text-xs leading-5 text-slate-400">{helperText}</p> : null}
    </label>
  );
}
