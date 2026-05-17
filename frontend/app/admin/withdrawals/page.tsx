"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, RefreshCw, X } from "lucide-react";

import {
  apiAdminApproveWithdrawal,
  apiAdminListPendingWithdrawals,
  apiAdminRejectWithdrawal,
  extractApiError,
} from "@/lib/api";
import { Withdrawal } from "@/lib/types";
import { formatDateTime, formatVND } from "@/lib/utils";

export default function AdminWithdrawalsPage() {
  const [items, setItems] = useState<Withdrawal[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiAdminListPendingWithdrawals(1, 50);
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

  async function approve(w: Withdrawal) {
    if (
      !window.confirm(
        `Đã chuyển ${formatVND(w.amount)} cho user #${w.user_id}?\n\n` +
          `TK: ${w.account_number} - ${w.account_name}` +
          (w.bank_name ? ` (${w.bank_name})` : "") +
          `\n\nXác nhận approve sẽ ghi vào lịch sử.`,
      )
    )
      return;
    setBusy(w.id);
    setMsg(null);
    try {
      await apiAdminApproveWithdrawal(w.id);
      setMsg(`✅ Đã approve withdrawal #${w.id}`);
      await load();
    } catch (e) {
      setError(extractApiError(e, "Approve thất bại"));
    } finally {
      setBusy(null);
    }
  }

  async function reject(w: Withdrawal) {
    const reason = window.prompt(
      `Reject lệnh rút #${w.id} (${formatVND(w.amount)})?\n\nLý do (sẽ hoàn lại tiền cho user):`,
      "",
    );
    if (reason === null) return;
    setBusy(w.id);
    setMsg(null);
    try {
      await apiAdminRejectWithdrawal(w.id, reason || undefined);
      setMsg(`↩️ Đã reject withdrawal #${w.id}, hoàn tiền cho user #${w.user_id}`);
      await load();
    } catch (e) {
      setError(extractApiError(e, "Reject thất bại"));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Lệnh rút chờ duyệt</h2>
          <p className="text-sm text-zinc-500">
            Tổng: <span className="text-white">{total}</span>
          </p>
        </div>
        <button onClick={load} className="btn-ghost px-3 py-1.5 text-sm" disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          <span className="ml-1">Tải lại</span>
        </button>
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
        <div className="card text-center text-zinc-500">Không có lệnh rút pending nào.</div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-zinc-800">
          <table className="w-full min-w-[800px] text-sm">
            <thead className="bg-zinc-900 text-left text-xs uppercase text-zinc-400">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">User</th>
                <th className="px-3 py-2">Số tiền</th>
                <th className="px-3 py-2">Tài khoản</th>
                <th className="px-3 py-2">Tạo lúc</th>
                <th className="px-3 py-2 text-right">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {items.map((w) => (
                <tr key={w.id} className="hover:bg-zinc-900/40">
                  <td className="px-3 py-2 font-mono">#{w.id}</td>
                  <td className="px-3 py-2">#{w.user_id}</td>
                  <td className="px-3 py-2 font-semibold text-gold">{formatVND(w.amount)}</td>
                  <td className="px-3 py-2">
                    <div className="font-mono text-zinc-200">{w.account_number}</div>
                    <div className="text-xs text-zinc-500">
                      {w.account_name}
                      {w.bank_name ? ` · ${w.bank_name}` : ""}
                    </div>
                  </td>
                  <td className="px-3 py-2 text-zinc-400">{formatDateTime(w.requested_at)}</td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex justify-end gap-1">
                      <button
                        onClick={() => approve(w)}
                        disabled={busy === w.id}
                        className="inline-flex items-center gap-1 rounded-md border border-emerald-700 bg-emerald-900/40 px-2.5 py-1 text-xs font-semibold text-emerald-300 hover:bg-emerald-900/70 disabled:opacity-50"
                      >
                        <Check className="h-3.5 w-3.5" />
                        Approve
                      </button>
                      <button
                        onClick={() => reject(w)}
                        disabled={busy === w.id}
                        className="inline-flex items-center gap-1 rounded-md border border-red-700 bg-red-900/40 px-2.5 py-1 text-xs font-semibold text-red-300 hover:bg-red-900/70 disabled:opacity-50"
                      >
                        <X className="h-3.5 w-3.5" />
                        Reject
                      </button>
                    </div>
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
