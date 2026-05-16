"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";

import { apiTelegramLinkToken, extractApiError } from "@/lib/api";
import { TelegramLinkToken } from "@/lib/types";
import { Protected } from "@/components/Protected";
import { useAuth } from "@/lib/store";
import { formatDateTime, formatVND } from "@/lib/utils";

export default function ProfilePage() {
  return (
    <Protected>
      <ProfileInner />
    </Protected>
  );
}

function ProfileInner() {
  const user = useAuth((s) => s.user);
  const [token, setToken] = useState<TelegramLinkToken | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const t = await apiTelegramLinkToken();
      setToken(t);
    } catch (err) {
      setError(extractApiError(err, "Không tạo được token"));
    } finally {
      setLoading(false);
    }
  }

  if (!user) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-2xl font-bold">Tài khoản</h1>

      <div className="card grid gap-3 sm:grid-cols-2">
        <Info label="Username" value={user.username} />
        <Info label="ID" value={`#${user.id}`} />
        <Info label="Số dư" value={formatVND(user.balance)} highlight />
        <Info label="Vai trò" value={user.is_admin ? "Admin" : "User"} />
        <Info label="Email" value={user.email || "—"} />
        <Info label="Phone" value={user.phone || "—"} />
        <Info label="Telegram ID" value={user.telegram_id ? String(user.telegram_id) : "Chưa liên kết"} />
        <Info label="Trạng thái" value={user.is_active ? "Hoạt động" : "Bị khóa"} />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold">Liên kết Telegram</h2>
        <p className="mt-1 text-sm text-zinc-400">
          Tạo token, sau đó vào Telegram bot và gửi <code>/link &lt;token&gt;</code> để liên kết.
        </p>
        {token ? (
          <div className="mt-3 flex items-center gap-3">
            <div className="flex-1 rounded-md border border-zinc-700 bg-zinc-950 px-4 py-3 font-mono text-xl tracking-widest">
              {token.token}
            </div>
            <button
              className="btn-secondary"
              onClick={async () => {
                await navigator.clipboard.writeText(token.token);
                setCopied(true);
                setTimeout(() => setCopied(false), 1500);
              }}
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              Copy
            </button>
          </div>
        ) : (
          <button onClick={generate} className="btn-primary mt-3" disabled={loading}>
            {loading ? "Đang tạo..." : "Tạo token liên kết"}
          </button>
        )}
        {token && (
          <p className="mt-2 text-xs text-zinc-500">
            Token hết hạn lúc {formatDateTime(token.expires_at)}.
          </p>
        )}
        {error && (
          <div className="mt-3 rounded-md border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}

function Info({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="rounded-md border border-zinc-800 bg-zinc-950/40 px-3 py-2">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className={`text-sm ${highlight ? "text-gold font-bold" : "text-zinc-100"}`}>{value}</div>
    </div>
  );
}
