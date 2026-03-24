import Link from "next/link";
import type { ReactNode } from "react";
import { Badge, Button } from "@legalos/ui";

const navigation = [
  { href: "/", label: "Home" },
  { href: "/login", label: "Login" },
  { href: "/matters", label: "Matters" }
];

export function AppShell({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <div className="mx-auto min-h-screen max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
      <div className="rounded-[2rem] border border-white/10 bg-[rgba(8,16,18,0.72)] shadow-card backdrop-blur">
        <header className="flex flex-col gap-4 border-b border-white/10 px-5 py-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-saffron-500/15 text-sm font-semibold text-amber-200">
                L
              </div>
              <div>
                <div className="text-sm font-medium tracking-[0.18em] text-white">LegalOS</div>
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">
                  India-first litigation operating system
                </div>
              </div>
            </div>
            <Badge variant="warning">Quote-lock enabled in the data model</Badge>
          </div>

          <nav className="flex flex-wrap gap-2">
            {navigation.map((item) => (
              <Button key={item.href} variant="ghost" size="sm" asChild>
                <Link href={item.href}>{item.label}</Link>
              </Button>
            ))}
          </nav>
        </header>

        <main className="px-5 py-6">{children}</main>
      </div>
    </div>
  );
}
