"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { apiLogin, apiRegister, extractApiError } from "@/lib/api";
import { useAuth } from "@/lib/store";

export default function RegisterPage() {
  const router = useRouter();
  const signIn = useAuth((s) => s.signIn);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await apiRegister({
        username: username.trim(),
        password,
        phone: phone.trim() || undefined,
        email: email.trim() || undefined,
      });
      // Auto-login sau khi register
      const res = await apiLogin(username.trim(), password);
      signIn(res.user, res.tokens);
      router.replace("/");
    } catch (err) {
      setError(extractApiError(err, "Đăng ký thất bại"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="card">
        <h1 className="text-2xl font-bold">Đăng ký</h1>
        <p className="mt-1 text-sm text-zinc-400">Tạo tài khoản miễn phí, không cần xác minh.</p>
        <form onSubmit={submit} className="mt-5 space-y-4">
          <div>
            <label className="label">Tên đăng nhập</label>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              minLength={3}
              maxLength={50}
              required
            />
            <p className="mt-1 text-xs text-zinc-500">Chỉ chữ, số, dấu gạch dưới (tối thiểu 3 ký tự).</p>
          </div>
          <div>
            <label className="label">Mật khẩu</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={6}
              maxLength={72}
              required
            />
          </div>
          <div>
            <label className="label">Số điện thoại (tùy chọn)</label>
            <input
              className="input"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              maxLength={15}
            />
          </div>
          <div>
            <label className="label">Email (tùy chọn)</label>
            <input
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              maxLength={100}
            />
          </div>
          {error && (
            <div className="rounded-md border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
              {error}
            </div>
          )}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Đang đăng ký..." : "Đăng ký"}
          </button>
        </form>
        <div className="mt-4 text-center text-sm text-zinc-400">
          Đã có tài khoản?{" "}
          <Link href="/login" className="text-brand hover:underline">
            Đăng nhập
          </Link>
        </div>
      </div>
    </div>
  );
}
