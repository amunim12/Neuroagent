import { AuthForm } from "@/components/auth-form";

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <AuthForm mode="register" />
    </main>
  );
}
