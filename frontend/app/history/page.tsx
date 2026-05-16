"use client";

import { useEffect, useState } from "react";

import { apiCancelBet, apiListBets, extractApiError } from "@/lib/api";
import { Bet } from "@/lib/types";
import { Protected } from "@/components/Protected";
import { formatDateTime, formatVND } from "@/lib/utils";

export default function HistoryPage() {
  return (
    <Protected>
      <HistoryInner />
    </Protected>
  );
}

function HistoryInner() {
  const [bets, setBets] = useState<Bet[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const limit = 20;

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiListBets({
        page,
        limit,
        status: statusFilter || undefined,
      });
      setBets(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(extractApiError(err, "Không tải được lịch sử"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, statusFilter]);

  async function cancel(id: number) {
    if (!confirm("Hủy lệnh cược này?")) return;
    try {
      await apiCancelBet(id);
      load();
    } catch (err) {
      alert(extractApiError(err, "Không thể hủy"));
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div>
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold">Lịch sử cược</h1>
          <p className="text-sm text-zinc-400">Tổng {total} lệnh.</p>
        </div>
        <select
          className="input w-40"
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
        >
          <option value="">Tất cả</option>
          <option value="pending">Chờ kết quả</option>
          <option value="won">Thắng</option>
          <option value="lost">Thua</option>
          <option value="cancelled">Đã hủy</option>
        </select>
      </div>

      {error && (
        <div className="mt-4 rounded-md border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="mt-4 overflow-x-auto rounded-xl border border-zinc-800">
        <table className="w-full min-w-[720px] text-sm">
          <thead className="bg-zinc-900 text-zinc-400">
            <tr>
              <th className="px-3 py-2 text-left">ID</th>
              <th className="px-3 py-2 text-left">Ngày xổ</th>
              <th className="px-3 py-2 text-left">Game</th>
              <th className="px-3 py-2 text-left">Loại</th>
              <th className="px-3 py-2 text-left">Số</th>
              <th className="px-3 py-2 text-right">Cược</th>
              <th className="px-3 py-2 text-right">Thắng</th>
              <th className="px-3 py-2 text-center">Trạng thái</th>
              <th className="px-3 py-2 text-right"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} className="px-3 py-6 text-center text-zinc-500">
                  Đang tải...
                </td>
              </tr>
            ) : bets.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-3 py-6 text-center text-zinc-500">
                  Chưa có lệnh cược nào.
                </td>
              </tr>
            ) : (
              bets.map((b) => (
                <tr key={b.id} className="border-t border-zinc-900 hover:bg-zinc-900/40">
                  <td className="px-3 py-2 font-mono text-zinc-300">#{b.id}</td>
                  <td className="px-3 py-2 text-zinc-300">{b.draw_date}</td>
                  <td className="px-3 py-2 text-zinc-300">{b.game_id}</td>
                  <td className="px-3 py-2 text-zinc-300">{b.bet_type_id}</td>
                  <td className="px-3 py-2 font-mono text-yellow-300">
                    {b.numbers.join(", ")}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">{formatVND(b.total_stake)}</td>
                  <td className="px-3 py-2 text-right font-mono">
                    {Number(b.win_amount) > 0 ? (
                      <span className="text-emerald-400">{formatVND(b.win_amount)}</span>
                    ) : (
                      <span className="text-zinc-600">—</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <StatusBadge status={b.status} />
                  </td>
                  <td className="px-3 py-2 text-right text-xs text-zinc-500">
                    {b.status === "pending" && (
                      <button onClick={() => cancel(b.id)} className="text-red-400 hover:underline">
                        Hủy
                      </button>
                    )}
                    <div className="text-[10px] text-zinc-600">{formatDateTime(b.placed_at)}</div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-zinc-400">
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
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    pending: "badge-yellow",
    won: "badge-green",
    lost: "badge-red",
    cancelled: "badge-gray",
  };
  const labels: Record<string, string> = {
    pending: "Chờ kết quả",
    won: "Thắng",
    lost: "Thua",
    cancelled: "Hủy",
  };
  return <span className={map[status] || "badge-gray"}>{labels[status] || status}</span>;
}
