import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { Button, Card } from "@legalos/ui";

export default function NotFoundPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-2xl">
        <Card className="space-y-5 text-center">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Not found</div>
          <h1 className="text-3xl font-semibold text-white">This matter or page is not available.</h1>
          <p className="text-sm leading-6 text-slate-300">
            The route was resolved, but the backend did not return a matching matter record yet.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Button asChild>
              <Link href="/">Return home</Link>
            </Button>
            <Button variant="secondary" asChild>
              <Link href="/login">Go to login</Link>
            </Button>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
