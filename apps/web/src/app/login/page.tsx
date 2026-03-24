import { AppShell } from "@/components/app-shell";
import { LoginForm } from "@/components/login-form";

export default function LoginPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-lg">
        <LoginForm />
      </div>
    </AppShell>
  );
}
