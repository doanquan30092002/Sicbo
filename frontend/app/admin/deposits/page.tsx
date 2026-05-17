"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, RefreshCw } from "lucide-react";

import {
  apiAdminConfirmDeposit,
  apiAdminListPendingDeposits,
  extractApiError,
} from "@/lib/api";
import { Deposit } from "@/lib/types";
import { formatDateTime, formatVND } from "@/lib/utils";

export default function AdminDepositsPage() {
  const [items, setItems] = useState<Deposit[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState<number | null>(null);
  const [confirmMsg, setConfirmMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiAdminListPendingDeposits(1, 50);
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

  async function handleConfirm(d: Deposit) {
    const note = window.prompt(
      `Xác nhận đã nhận ${formatVND(d.amount)} với mã CK "${d.transfer_content}" từ user #${d.user_id}?\n\nNhập ghi chú (tuỳ chọn):`,
      "",
    );
    if (note === null) return; // user pressed Cancel

    setConfirming(d.id);
    setConfirmMsg(null);
    try {
      await apiAdminConfirmDeposit(d.id, { note: note || undefined });
      setConfirmMsg(`✅ Đã confirm deposit #${d.id} (+${formatVND(d.amount)} cho user #${d.user_id})`);
      await load();
    } catch (e) {
      setError(extractApiError(e, "Confirm thất bại"));
    } finally {
      setConfirming(null);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Lệnh nạp chờ xác nhận</h2>
          <p className="text-sm text-zinc-500">
            Tổng: <span className="text-white">{total}</span>
          </p>
        </div>
        <button onClick={load} className="btn-ghost px-3 py-1.5 text-sm" disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          <span className="ml-1">Tải lại</span>
        </button>
      </div>

      {confirmMsg && (
        <div className="rounded-md border border-emerald-800 bg-emerald-900/30 p-3 text-sm text-emerald-300">
          {confirmMsg}
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
        <div className="card text-center text-zinc-500">Không có lệnh nạp pending nào.</div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-zinc-800">
          <table className="w-full min-w-[700px] text-sm">
            <thead className="bg-zinc-900 text-left text-xs uppercase text-zinc-400">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">User</th>
                <th className="px-3 py-2">Số tiền</th>
                <th className="px-3 py-2">Mã CK</th>
                <th className="px-3 py-2">Phương thức</th>
                <th className="px-3 py-2">Tạo lúc</th>
                <th className="px-3 py-2 text-right">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {items.map((d) => (
                <tr key={d.id} className="hover:bg-zinc-900/40">
                  <td className="px-3 py-2 font-mono">#{d.id}</td>
                  <td className="px-3 py-2">#{d.user_id}</td>
                  <td className="px-3 py-2 font-semibold text-gold">{formatVND(d.amount)}</td>
                  <td className="px-3 py-2 font-mono text-brand">{d.transfer_content}</td>
                  <td className="px-3 py-2 text-zinc-400">{d.payment_method}</td>
                  <td className="px-3 py-2 text-zinc-400">{formatDateTime(d.created_at)}</td>
                  <td className="px-3 py-2 text-right">
                    <button
                      onClick={() => handleConfirm(d)}
                      disabled={confirming === d.id}
                      className="inline-flex items-center gap-1 rounded-md border border-emerald-700 bg-emerald-900/40 px-2.5 py-1 text-xs font-semibold text-emerald-300 hover:bg-emerald-900/70 disabled:opacity-50"
                    >
                      <Check className="h-3.5 w-3.5" />
                      {confirming === d.id ? "Đang..." : "Xác nhận"}
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
