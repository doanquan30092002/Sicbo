"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, RefreshCw, Search } from "lucide-react";

import { apiAdminCreditDirect, apiAdminListUsers, extractApiError } from "@/lib/api";
import { User } from "@/lib/types";
import { formatDateTime, formatVND } from "@/lib/utils";

export default function AdminUsersPage() {
  const [items, setItems] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  const load = useCallback(async (q = "") => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiAdminListUsers({ search: q || undefined, page: 1, limit: 50 });
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(extractApiError(e, "Lỗi tải danh sách"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function credit(u: User) {
    const amountStr = window.prompt(`Cộng tiền cho user #${u.id} (${u.username})\n\nNhập số tiền (VND):`, "");
    if (!amountStr) return;
    const amount = Number(amountStr.replace(/[,\s]/g, ""));
    if (!Number.isFinite(amount) || amount <= 0) {
      setError("Số tiền không hợp lệ.");
      return;
    }
    const note = window.prompt(`Ghi chú (tuỳ chọn) — cộng ${formatVND(amount)} cho ${u.username}:`, "");
    if (note === null) return;

    setBusy(u.id);
    setMsg(null);
    try {
      await apiAdminCreditDirect({ user_id: u.id, amount, note: note || undefined });
      setMsg(`✅ Đã cộng ${formatVND(amount)} cho user #${u.id} (${u.username})`);
      await load(search);
    } catch (e) {
      setError(extractApiError(e, "Credit thất bại"));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold">Người dùng</h2>
          <p className="text-sm text-zinc-500">
            Tổng: <span className="text-white">{total}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <div className="flex items-center gap-1 rounded-md border border-zinc-800 bg-zinc-950 px-2">
            <Search className="h-4 w-4 text-zinc-500" />
            <input
              className="w-48 bg-transparent py-1.5 text-sm outline-none"
              placeholder="Tìm username, phone, email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") load(search);
              }}
            />
          </div>
          <button onClick={() => load(search)} className="btn-ghost px-3 py-1.5 text-sm" disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {msg && (
        <div className="rounded-md border border-emerald-800 bg-emerald-900/30 p-3 text-sm text-emerald-300">
          {msg}
        </div>
      )}

      {error && (
        <div className="rounded-md border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-zinc-500">Đang tải...</div>
      ) : items.length === 0 ? (
        <div className="card text-center text-zinc-500">Không tìm thấy user.</div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-zinc-800">
          <table className="w-full min-w-[800px] text-sm">
            <thead className="bg-zinc-900 text-left text-xs uppercase text-zinc-400">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Username</th>
                <th className="px-3 py-2">Balance</th>
                <th className="px-3 py-2">Liên hệ</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Tạo lúc</th>
                <th className="px-3 py-2 text-right">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {items.map((u) => (
                <tr key={u.id} className="hover:bg-zinc-900/40">
                  <td className="px-3 py-2 font-mono">#{u.id}</td>
                  <td className="px-3 py-2">
                    <div className="font-semibold">{u.username}</div>
                    {u.is_admin && (
                      <span className="rounded bg-red-900/40 px-1 text-[10px] uppercase text-red-300">
                        admin
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 font-semibold text-gold">{formatVND(u.balance)}</td>
                  <td className="px-3 py-2 text-xs text-zinc-400">
                    {u.phone && <div>📞 {u.phone}</div>}
                    {u.email && <div>✉ {u.email}</div>}
                    {u.telegram_username && <div>💬 @{u.telegram_username}</div>}
                  </td>
                  <td className="px-3 py-2">
                    {u.is_active ? (
                      <span className="rounded bg-emerald-900/40 px-2 py-0.5 text-xs text-emerald-300">
                        active
                      </span>
                    ) : (
                      <span className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400">
                        khóa
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-xs text-zinc-500">{formatDateTime(u.created_at)}</td>
                  <td className="px-3 py-2 text-right">
                    <button
                      onClick={() => credit(u)}
                      disabled={busy === u.id}
                      className="inline-flex items-center gap-1 rounded-md border border-brand/60 bg-brand/10 px-2.5 py-1 text-xs font-semibold text-brand hover:bg-brand/20 disabled:opacity-50"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Cộng tiền
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
