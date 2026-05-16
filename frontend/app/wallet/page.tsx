"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";

import { apiListTransactions, extractApiError } from "@/lib/api";
import { Transaction } from "@/lib/types";
import { Protected } from "@/components/Protected";
import { useAuth } from "@/lib/store";
import { formatDateTime, formatVND } from "@/lib/utils";

export default function WalletPage() {
  return (
    <Protected>
      <WalletInner />
    </Protected>
  );
}

function WalletInner() {
  const user = useAuth((s) => s.user);
  const [txs, setTxs] = useState<Transaction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const limit = 20;

  useEffect(() => {
    setLoading(true);
    apiListTransactions(page, limit)
      .then((d) => {
        setTxs(d.items);
        setTotal(d.total);
      })
      .catch((err) => setError(extractApiError(err, "Không tải được giao dịch")))
      .finally(() => setLoading(false));
  }, [page]);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="card">
          <div className="text-sm text-zinc-400">Số dư khả dụng</div>
          <div className="mt-2 text-3xl font-bold text-gold">
            {user ? formatVND(user.balance) : "—"}
          </div>
          <div className="mt-3 text-xs text-zinc-500">Cập nhật theo giao dịch gần nhất.</div>
        </div>
        <Link href="/wallet/deposit" className="card transition hover:border-emerald-700">
          <div className="flex items-center gap-3">
            <ArrowDown className="h-6 w-6 text-emerald-400" />
            <div>
              <div className="font-semibold">Nạp tiền</div>
              <div className="text-xs text-zinc-400">Chuyển khoản bank / MoMo qua SePay</div>
            </div>
          </div>
        </Link>
        <Link href="/wallet/withdraw" className="card transition hover:border-brand">
          <div className="flex items-center gap-3">
            <ArrowUp className="h-6 w-6 text-brand" />
            <div>
              <div className="font-semibold">Rút tiền</div>
              <div className="text-xs text-zinc-400">Yêu cầu rút, admin duyệt thủ công</div>
            </div>
          </div>
        </Link>
      </div>

      <div>
        <h2 className="text-lg font-semibold">Lịch sử giao dịch</h2>
        {error && (
          <div className="mt-2 rounded-md border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
            {error}
          </div>
        )}
        <div className="mt-3 overflow-x-auto rounded-xl border border-zinc-800">
          <table className="w-full min-w-[640px] text-sm">
            <thead className="bg-zinc-900 text-zinc-400">
              <tr>
                <th className="px-3 py-2 text-left">Thời gian</th>
                <th className="px-3 py-2 text-left">Loại</th>
                <th className="px-3 py-2 text-right">Số tiền</th>
                <th className="px-3 py-2 text-right">Sau giao dịch</th>
                <th className="px-3 py-2 text-left">Ghi chú</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-zinc-500">
                    Đang tải...
                  </td>
                </tr>
              ) : txs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-zinc-500">
                    Chưa có giao dịch nào.
                  </td>
                </tr>
              ) : (
                txs.map((t) => (
                  <tr key={t.id} className="border-t border-zinc-900">
                    <td className="px-3 py-2 text-zinc-300">{formatDateTime(t.created_at)}</td>
                    <td className="px-3 py-2 text-zinc-300">{t.type}</td>
                    <td
                      className={`px-3 py-2 text-right font-mono ${
                        Number(t.amount) >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {Number(t.amount) >= 0 ? "+" : ""}
                      {formatVND(t.amount)}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-zinc-200">
                      {formatVND(t.balance_after)}
                    </td>
                    <td className="px-3 py-2 text-xs text-zinc-500">{t.description || "—"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="mt-3 flex items-center justify-between text-sm text-zinc-400">
          <div>
            Trang {page} / {totalPages}
          </div>
          <div className="flex gap-2">
            <button
              className="btn-secondary"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              ← Trước
            </button>
            <button
              className="btn-secondary"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Sau →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
