"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Lock, Mail, AlertCircle, Loader2 } from "lucide-react";
import { useAuth } from "@/components/providers/AuthProvider";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setError(null);

      if (!email.trim() || !password.trim()) {
        setError("Email and password are required.");
        return;
      }

      setLoading(true);
      try {
        await login({ email: email.trim(), password });
        router.replace("/");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Login failed. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    [email, password, login, router]
  );

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0a0f1e]">
      {/* Animated background gradient orbs */}
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden="true"
      >
        <div className="absolute -left-40 -top-40 h-[600px] w-[600px] rounded-full bg-[#1e40af]/20 blur-3xl animate-pulse-slow" />
        <div className="absolute -bottom-40 -right-40 h-[500px] w-[500px] rounded-full bg-[#7c3aed]/20 blur-3xl animate-pulse-slow [animation-delay:2s]" />
        <div className="absolute left-1/2 top-1/2 h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#0ea5e9]/10 blur-3xl animate-pulse-slow [animation-delay:4s]" />
        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      {/* Login card */}
      <div className="relative z-10 w-full max-w-md px-6">
        {/* Logo / Brand */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-[#1e40af] to-[#7c3aed] shadow-[0_0_40px_rgba(124,58,237,0.4)]">
            <svg
              viewBox="0 0 32 32"
              fill="none"
              className="h-9 w-9"
              aria-hidden="true"
            >
              <circle cx="16" cy="16" r="14" fill="rgba(255,255,255,0.1)" />
              <path
                d="M10 20 L16 10 L22 20"
                stroke="white"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="16" cy="20.5" r="2" fill="white" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Orzen Vision
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Enterprise Retail Analytics Platform
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-xl">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-white">Sign in to your account</h2>
            <p className="mt-1 text-sm text-slate-400">
              Enter your credentials to access the dashboard
            </p>
          </div>

          {/* Error banner */}
          {error && (
            <div
              role="alert"
              className="mb-5 flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            {/* Email */}
            <div>
              <label
                htmlFor="login-email"
                className="mb-1.5 block text-sm font-medium text-slate-300"
              >
                Email address
              </label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  id="login-email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  placeholder="admin@orzen.io"
                  className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-10 pr-4 text-sm text-white placeholder-slate-600 transition-all duration-200 focus:border-[#1e40af]/70 focus:bg-white/8 focus:outline-none focus:ring-2 focus:ring-[#1e40af]/40 disabled:opacity-50"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="login-password"
                className="mb-1.5 block text-sm font-medium text-slate-300"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-10 pr-11 text-sm text-white placeholder-slate-600 transition-all duration-200 focus:border-[#1e40af]/70 focus:bg-white/8 focus:outline-none focus:ring-2 focus:ring-[#1e40af]/40 disabled:opacity-50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-0.5 text-slate-500 transition-colors hover:text-slate-300 focus:outline-none focus:ring-2 focus:ring-[#1e40af]/40"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="group relative mt-2 w-full overflow-hidden rounded-xl bg-gradient-to-r from-[#1e40af] to-[#7c3aed] px-6 py-3 text-sm font-semibold text-white shadow-[0_4px_20px_rgba(124,58,237,0.4)] transition-all duration-300 hover:shadow-[0_4px_30px_rgba(124,58,237,0.6)] hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-[#7c3aed]/60 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <span
                className={`flex items-center justify-center gap-2 transition-opacity ${
                  loading ? "opacity-0" : "opacity-100"
                }`}
              >
                Sign in
              </span>
              {loading && (
                <span className="absolute inset-0 flex items-center justify-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Signing in…
                </span>
              )}
            </button>
          </form>

          {/* Footer note */}
          <p className="mt-6 text-center text-xs text-slate-600">
            Contact your system administrator to request access.
          </p>
        </div>

        {/* Bottom branding */}
        <p className="mt-6 text-center text-xs text-slate-700">
          © {new Date().getFullYear()} Orzen Vision · Enterprise Edition
        </p>
      </div>

      <style jsx>{`
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.7; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.08); }
        }
        .animate-pulse-slow {
          animation: pulse-slow 8s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
