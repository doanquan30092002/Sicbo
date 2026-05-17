"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import { apiLogin, extractApiError } from "@/lib/api";
import { useAuth } from "@/lib/store";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const signIn = useAuth((s) => s.signIn);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await apiLogin(username.trim(), password);
      signIn(res.user, res.tokens);
      const next = params.get("next") || "/";
      router.replace(next);
    } catch (err) {
      setError(extractApiError(err, "Đăng nhập thất bại"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="card">
        <h1 className="text-2xl font-bold">Đăng nhập</h1>
        <p className="mt-1 text-sm text-zinc-400">Đăng nhập để đặt cược và quản lý ví.</p>
        <form onSubmit={submit} className="mt-5 space-y-4">
          <div>
            <label className="label">Tên đăng nhập</label>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
              minLength={3}
            />
          </div>
          <div>
            <label className="label">Mật khẩu</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              minLength={6}
            />
          </div>
          {error && (
            <div className="rounded-md border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
              {error}
            </div>
          )}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Đang đăng nhập..." : "Đăng nhập"}
          </button>
        </form>
        <div className="mt-4 text-center text-sm text-zinc-400">
          Chưa có tài khoản?{" "}
          <Link href="/register" className="text-brand hover:underline">
            Đăng ký
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-md"><div className="card">Đang tải...</div></div>}>
      <LoginForm />
    </Suspense>
  );
}
