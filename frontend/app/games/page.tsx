"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiListGames } from "@/lib/api";
import { Game } from "@/lib/types";

export default function GamesPage() {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiListGames()
      .then(setGames)
      .catch(() => setError("Không tải được danh sách game. Kiểm tra backend."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold">Chọn game</h1>
      <p className="mt-1 text-sm text-zinc-400">Chọn 1 game để đặt cược cho phiên hôm nay.</p>

      {error && (
        <div className="mt-4 rounded-md border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="mt-6 text-zinc-500">Đang tải...</div>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {games.map((g) => (
            <Link
              key={g.game_id}
              href={`/games/${g.game_id}`}
              className="card transition hover:border-brand"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-xs uppercase text-zinc-500">#{g.game_id}</div>
                  <h3 className="text-lg font-bold">{g.game_name}</h3>
                </div>
                <span className="badge badge-green">Active</span>
              </div>
              <div className="mt-3 text-xs text-zinc-500">
                Cutoff {g.cutoff_time} · Kết quả {g.result_time}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {g.bet_types.map((bt) => (
                  <span key={bt.type_id} className="badge badge-gray">
                    {bt.display_name} · 1:{bt.odds}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
