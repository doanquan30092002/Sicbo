"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, Trophy, Wallet, Clock, Shield } from "lucide-react";

import { apiListGames } from "@/lib/api";
import { Game } from "@/lib/types";
import { useAuth } from "@/lib/store";

export default function HomePage() {
  const user = useAuth((s) => s.user);
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    apiListGames()
      .then((g) => mounted && setGames(g))
      .catch(() => {})
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="space-y-10">
      <section className="card relative overflow-hidden">
        <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-brand/20 blur-3xl" />
        <div className="relative">
          <span className="badge badge-yellow border-yellow-700 bg-yellow-900/30">XSMB · 18:30 mỗi ngày</span>
          <h1 className="mt-3 text-3xl font-bold sm:text-4xl">
            Nạp <span className="text-gold">1 phút</span>, rút <span className="text-brand">1 giây</span>
          </h1>
          <p className="mt-2 max-w-xl text-zinc-400">
            Đặt cược Lô, Đề, Xiên dựa trên kết quả Xổ Số Miền Bắc. Hệ thống tự lấy kết quả lúc 18:30, tính tiền tự động.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/games" className="btn-primary">
              Đặt cược ngay <ArrowRight className="h-4 w-4" />
            </Link>
            {!user && (
              <Link href="/register" className="btn-secondary">
                Đăng ký tài khoản
              </Link>
            )}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Feature icon={Clock} title="Cutoff 18:10" desc="Đặt cược tới sát giờ xổ" />
        <Feature icon={Trophy} title="Tỉ lệ cao" desc="Đề 1:75, Xiên 3 1:40" />
        <Feature icon={Wallet} title="Nạp/Rút nhanh" desc="SePay bank + MoMo" />
        <Feature icon={Shield} title="Minh bạch" desc="Đối chiếu công khai XSMB" />
      </section>

      <section>
        <div className="mb-3 flex items-end justify-between">
          <h2 className="text-xl font-semibold">Các game đang hoạt động</h2>
          <Link href="/games" className="text-sm text-zinc-400 hover:text-white">
            Xem tất cả →
          </Link>
        </div>
        {loading ? (
          <div className="text-sm text-zinc-500">Đang tải...</div>
        ) : games.length === 0 ? (
          <div className="card text-sm text-zinc-500">
            Chưa có game active. Hãy kiểm tra backend hoặc <code>GameRegistry</code>.
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {games.map((g) => (
              <GameCard key={g.game_id} game={g} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function Feature({
  icon: Icon,
  title,
  desc,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  desc: string;
}) {
  return (
    <div className="card flex flex-col items-start gap-2">
      <Icon className="h-5 w-5 text-gold" />
      <div className="font-semibold">{title}</div>
      <div className="text-xs text-zinc-400">{desc}</div>
    </div>
  );
}

function GameCard({ game }: { game: Game }) {
  return (
    <Link href={`/games/${game.game_id}`} className="card group transition hover:border-brand">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-zinc-400">#{game.game_id}</div>
          <div className="text-xl font-bold">{game.game_name}</div>
        </div>
        <span className="badge badge-green">Active</span>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {game.bet_types.map((bt) => (
          <span key={bt.type_id} className="badge badge-gray">
            {bt.display_name} · 1:{bt.odds}
          </span>
        ))}
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-zinc-500">
        <span>Cutoff {game.cutoff_time} · Kết quả {game.result_time}</span>
        <span className="text-brand opacity-0 transition group-hover:opacity-100">Đặt cược →</span>
      </div>
    </Link>
  );
}
