"use client";

import { useState, type ChangeEvent, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button, Card, Field, Input } from "@legalos/ui";
import { setAuthToken } from "@/lib/auth";
import { createBrowserApiClient } from "@/lib/api/client";

export function LoginForm() {
  const router = useRouter();
  const api = createBrowserApiClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const result = await api.login({
        email,
        password
      });
      setAuthToken(result.access_token);
      const matters = await createBrowserApiClient(result.access_token).getMatters();
      if (matters.ok && matters.data[0]) {
        router.push(`/matters/${matters.data[0].id}`);
        return;
      }
      router.push("/matters");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Card className="space-y-6 border-white/10 bg-white/5 p-6 backdrop-blur">
      <div className="space-y-2">
        <div className="text-xs uppercase tracking-[0.24em] text-slate-400">Access control</div>
        <h1 className="text-3xl font-semibold text-white">Sign in to a matter workspace</h1>
        <p className="text-sm leading-6 text-slate-300">
          Authenticate against the FastAPI backend and open the seeded matter workspace from the matter index.
        </p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <Field label="Email address">
          <Input
            type="email"
            value={email}
            onChange={(event: ChangeEvent<HTMLInputElement>) => setEmail(event.target.value)}
            required
          />
        </Field>

        <Field label="Password">
          <Input
            type="password"
            value={password}
            onChange={(event: ChangeEvent<HTMLInputElement>) => setPassword(event.target.value)}
            required
          />
        </Field>

        {error ? (
          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-100">
            {error}
          </div>
        ) : null}

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Signing in..." : "Continue"}
        </Button>
      </form>
    </Card>
  );
}
