import { AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return (
    <main className="relative flex min-h-screen items-center justify-center bg-dot-grid px-4">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background: "radial-gradient(ellipse 60% 50% at 50% 40%, rgba(99,102,241,0.1) 0%, transparent 70%)",
        }}
      />
      <div className="relative w-full max-w-sm">
        <AuthForm mode="register" />
      </div>
    </main>
  );
}
