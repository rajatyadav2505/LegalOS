import { cloneElement, isValidElement, type ButtonHTMLAttributes, type ReactElement, type ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "destructive";
type ButtonSize = "sm" | "md";

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-saffron-500 text-ink-950 hover:bg-saffron-400 focus-visible:outline-saffron-300",
  secondary:
    "border border-white/10 bg-white/5 text-white hover:border-white/20 hover:bg-white/10 focus-visible:outline-white/60",
  ghost: "text-slate-200 hover:bg-white/5 focus-visible:outline-white/60",
  destructive:
    "border border-red-500/30 bg-red-500/15 text-red-100 hover:bg-red-500/20 focus-visible:outline-red-300"
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-9 px-3 text-sm",
  md: "h-11 px-4 text-sm"
};

export function Button({
  className = "",
  variant = "primary",
  size = "md",
  asChild = false,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  asChild?: boolean;
  children: ReactNode;
}) {
  const classes = [
    "inline-flex items-center justify-center rounded-2xl font-medium transition-colors",
    "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2",
    variantStyles[variant],
    sizeStyles[size],
    className
  ]
    .filter(Boolean)
    .join(" ");

  if (asChild && isValidElement(children)) {
    return cloneElement(
      children as ReactElement<Record<string, unknown>>,
      {
        ...props,
        className: [classes, ((children.props as Record<string, unknown>).className as string | undefined) ?? ""]
          .filter(Boolean)
          .join(" ")
      } as Record<string, unknown>
    );
  }

  return (
    <button
      className={classes}
      {...props}
    >
      {children}
    </button>
  );
}
