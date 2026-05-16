"use client";

import { useEffect, useState } from "react";

import { apiListGames, apiResultRecent } from "@/lib/api";
import { Game, GameResult } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";

export default function ResultsPage() {
  const [games, setGames] = useState<Game[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [results, setResults] = useState<GameResult[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiListGames().then((g) => {
      setGames(g);
      if (g[0]) setSelected(g[0].game_id);
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    apiResultRecent(selected, 7)
      .then((r) => setResults(r.items))
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, [selected]);

  return (
    <div>
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold">Kết quả gần đây</h1>
          <p className="text-sm text-zinc-400">7 ngày gần nhất.</p>
        </div>
        <select
          className="input w-40"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          {games.map((g) => (
            <option key={g.game_id} value={g.game_id}>
              {g.game_name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="mt-4 text-zinc-500">Đang tải...</div>
      ) : results.length === 0 ? (
        <div className="card mt-4 text-zinc-500">Chưa có kết quả.</div>
      ) : (
        <div className="mt-4 space-y-3">
          {results.map((r) => (
            <ResultCard key={r.id} result={r} />
          ))}
        </div>
      )}
    </div>
  );
}

function ResultCard({ result }: { result: GameResult }) {
  const data = result.parsed_data || {};
  const special = (data["special"] as string) || (data["giai_dac_biet"] as string) || "";
  const allLast2 = (data["all_last2"] as string[]) || [];

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs text-zinc-500">{result.game_id}</div>
          <div className="text-lg font-bold">{result.draw_date}</div>
          <div className="text-xs text-zinc-500">Fetched {formatDateTime(result.fetched_at)}</div>
        </div>
        {special && (
          <div className="rounded-md bg-brand/15 px-3 py-1 text-center">
            <div className="text-[10px] uppercase text-brand">Đặc biệt</div>
            <div className="font-mono text-xl font-bold text-white">{special}</div>
          </div>
        )}
      </div>
      {allLast2.length > 0 && (
        <div className="mt-3">
          <div className="text-xs text-zinc-500">2 số cuối ({allLast2.length})</div>
          <div className="mt-1 flex flex-wrap gap-1 font-mono text-xs">
            {allLast2.map((n, i) => (
              <span key={i} className="rounded bg-zinc-800 px-1.5 py-0.5">
                {n}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
