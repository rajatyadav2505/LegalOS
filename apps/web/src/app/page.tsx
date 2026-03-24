import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { Button } from "@legalos/ui";

const highlights = [
  {
    label: "Research",
    value: "Verified citations and quote-lock"
  },
  {
    label: "Documents",
    value: "Upload PDF, DOCX, images, and bundles"
  },
  {
    label: "Strategy",
    value: "Bounded issue-level decision support"
  }
];

export default function HomePage() {
  return (
    <AppShell>
      <section className="grid gap-8 lg:grid-cols-[1.4fr_0.9fr]">
        <div className="space-y-8">
          <div className="space-y-5">
            <div className="inline-flex rounded-full border border-white/10 bg-white/5 px-4 py-1 text-xs uppercase tracking-[0.24em] text-amber-200">
              Litigation operating system
            </div>
            <div className="space-y-4">
              <h1 className="max-w-3xl text-4xl font-semibold leading-tight text-white sm:text-5xl">
                Research, bundle intelligence, drafting, and hearing prep in one source-grounded workspace.
              </h1>
              <p className="max-w-2xl text-base leading-7 text-slate-300">
                LegalOS is scaffolded for advocates, chambers, and legal-aid teams that need provenance-first
                workflows, exact quote spans, and disciplined matter operations.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button asChild>
                <Link href="/login">Open login</Link>
              </Button>
              <Button variant="secondary" asChild>
                <Link href="/matters">Open matter index</Link>
              </Button>
              <Button variant="ghost" asChild>
                <Link href="/matters">Go to workspace</Link>
              </Button>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {highlights.map((item) => (
              <article
                key={item.label}
                className="rounded-2xl border border-white/10 bg-white/5 p-4 shadow-card backdrop-blur"
              >
                <div className="text-xs uppercase tracking-[0.22em] text-slate-400">{item.label}</div>
                <div className="mt-3 text-sm leading-6 text-slate-100">{item.value}</div>
              </article>
            ))}
          </div>
        </div>

        <aside className="space-y-4 rounded-3xl border border-white/10 bg-[rgba(9,19,21,0.82)] p-6 shadow-card backdrop-blur">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Phase 0 / 1 scaffold</div>
          <div className="space-y-4">
            <div>
              <div className="text-lg font-medium text-white">Front-end surfaces</div>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Login, matter index, upload flow, and research workspace are wired to the concrete FastAPI endpoints.
              </p>
            </div>
            <div className="rounded-2xl border border-saffron-500/20 bg-saffron-500/10 p-4 text-sm leading-6 text-amber-100">
              Exact quotes only render from stored source spans. Research actions are structured for later saving and
              memo export.
            </div>
          </div>
        </aside>
      </section>
    </AppShell>
  );
}
