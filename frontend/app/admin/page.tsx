"use client";

import { useEffect, useState } from "react";
import { Users, AlertTriangle, Dices, TrendingUp, TrendingDown } from "lucide-react";

import { apiAdminStats, extractApiError } from "@/lib/api";
import { AdminStats } from "@/lib/types";
import { formatVND } from "@/lib/utils";

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    apiAdminStats()
      .then((s) => alive && setStats(s))
      .catch((e) => alive && setError(extractApiError(e, "Lỗi tải dữ liệu")))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  if (loading) return <div className="text-zinc-500">Đang tải...</div>;
  if (error) return <div className="text-red-400">{error}</div>;
  if (!stats) return null;

  const cards = [
    { label: "Tổng người dùng", value: stats.total_users, icon: Users, color: "text-blue-400" },
    {
      label: "Lệnh rút chờ duyệt",
      value: stats.total_pending_withdrawals,
      icon: AlertTriangle,
      color: "text-yellow-400",
    },
    { label: "Cược hôm nay", value: stats.today_bets, icon: Dices, color: "text-brand" },
    {
      label: "Tổng cược hôm nay",
      value: formatVND(stats.today_total_stake),
      icon: TrendingUp,
      color: "text-emerald-400",
    },
    {
      label: "Tổng trả thưởng hôm nay",
      value: formatVND(stats.today_total_payout),
      icon: TrendingDown,
      color: "text-rose-400",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <div key={c.label} className="card">
            <div className="flex items-center justify-between">
              <div className="text-sm text-zinc-400">{c.label}</div>
              <Icon className={`h-5 w-5 ${c.color}`} />
            </div>
            <div className="mt-2 text-2xl font-bold">{c.value}</div>
          </div>
        );
      })}
    </div>
  );
}
