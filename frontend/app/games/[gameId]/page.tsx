"use client";

import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  apiCutoffStatus,
  apiListGames,
  apiPlaceBet,
  extractApiError,
} from "@/lib/api";
import { BetType, CutoffStatus, Game } from "@/lib/types";
import { useAuth } from "@/lib/store";
import { formatCountdown, formatVND } from "@/lib/utils";

export default function GameDetailPage() {
  const params = useParams<{ gameId: string }>();
  const gameId = params?.gameId as string;
  const router = useRouter();

  const user = useAuth((s) => s.user);
  const hydrated = useAuth((s) => s.hydrated);
  const setUser = useAuth((s) => s.setUser);

  const [game, setGame] = useState<Game | null>(null);
  const [status, setStatus] = useState<CutoffStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [betTypeId, setBetTypeId] = useState<string>("");
  const [numbers, setNumbers] = useState<string>("");
  const [stake, setStake] = useState<string>("10000");
  const [points, setPoints] = useState<string>("1");
  const [submitting, setSubmitting] = useState(false);
  const [submitMsg, setSubmitMsg] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    let mounted = true;
    apiListGames()
      .then((games) => {
        const g = games.find((x) => x.game_id === gameId) || null;
        if (mounted) {
          setGame(g);
          if (g && g.bet_types[0]) setBetTypeId(g.bet_types[0].type_id);
        }
      })
      .catch(() => setError("Không tải được thông tin game."))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, [gameId]);

  useEffect(() => {
    let mounted = true;
    let timer: ReturnType<typeof setInterval> | null = null;

    async function tick() {
      try {
        const s = await apiCutoffStatus(gameId);
        if (mounted) setStatus(s);
      } catch {
        // ignore
      }
    }

    tick();
    timer = setInterval(() => {
      setStatus((prev) =>
        prev
          ? { ...prev, seconds_until_cutoff: Math.max(prev.seconds_until_cutoff - 1, 0), is_open: prev.seconds_until_cutoff - 1 > 0 }
          : prev,
      );
    }, 1000);

    const refreshTimer = setInterval(tick, 30000);

    return () => {
      mounted = false;
      if (timer) clearInterval(timer);
      clearInterval(refreshTimer);
    };
  }, [gameId]);

  const currentBetType: BetType | undefined = useMemo(
    () => game?.bet_types.find((b) => b.type_id === betTypeId),
    [game, betTypeId],
  );

  const parsedNumbers = useMemo(
    () =>
      numbers
        .split(/[\s,;]+/)
        .map((s) => s.trim())
        .filter(Boolean),
    [numbers],
  );

  const stakeNum = Number(stake) || 0;
  const pointsNum = Number(points) || 1;
  const totalStake = stakeNum * pointsNum * parsedNumbers.length;
  const oddsNum = currentBetType ? Number(currentBetType.odds) : 0;
  const potential = totalStake * oddsNum;

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!user) {
      router.push(`/login?next=/games/${gameId}`);
      return;
    }
    if (!currentBetType) return;
    if (parsedNumbers.length < currentBetType.min_numbers || parsedNumbers.length > currentBetType.max_numbers) {
      setSubmitMsg({
        ok: false,
        text: `Bet "${currentBetType.display_name}" yêu cầu ${currentBetType.min_numbers}–${currentBetType.max_numbers} số.`,
      });
      return;
    }
    setSubmitting(true);
    setSubmitMsg(null);
    try {
      const bet = await apiPlaceBet({
        game_id: gameId,
        bet_type_id: betTypeId,
        numbers: parsedNumbers,
        stake_per_point: stakeNum,
        points: pointsNum,
      });
      setSubmitMsg({
        ok: true,
        text: `Đặt cược thành công! #${bet.id} · Tổng cược ${formatVND(bet.total_stake)} · Có thể thắng ${formatVND(bet.potential_win)}`,
      });
      setNumbers("");
      if (user) setUser({ ...user, balance: String(Number(user.balance) - Number(bet.total_stake)) });
    } catch (err) {
      setSubmitMsg({ ok: false, text: extractApiError(err, "Đặt cược thất bại") });
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="text-zinc-500">Đang tải...</div>;
  if (error || !game) return <div className="text-red-400">{error || "Game không tồn tại."}</div>;

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2 space-y-4">
        <div className="card">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-xs text-zinc-500">#{game.game_id}</div>
              <h1 className="text-2xl font-bold">{game.game_name}</h1>
              <div className="mt-1 text-sm text-zinc-400">
                Cutoff {game.cutoff_time} · Kết quả {game.result_time}
              </div>
            </div>
            <div className="text-right">
              {status && (
                <>
                  <div className={status.is_open ? "text-emerald-400" : "text-red-400"}>
                    {status.is_open ? "Đang mở cược" : "Đã đóng cược"}
                  </div>
                  <div className="font-mono text-2xl font-bold">
                    {formatCountdown(status.seconds_until_cutoff)}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        <form onSubmit={submit} className="card space-y-4">
          <h2 className="text-lg font-semibold">Đặt cược</h2>

          <div>
            <label className="label">Loại cược</label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {game.bet_types.map((bt) => (
                <button
                  type="button"
                  key={bt.type_id}
                  onClick={() => setBetTypeId(bt.type_id)}
                  className={`rounded-md border px-3 py-2 text-sm transition ${
                    bt.type_id === betTypeId
                      ? "border-brand bg-brand/15 text-white"
                      : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-zinc-500"
                  }`}
                >
                  <div className="font-medium">{bt.display_name}</div>
                  <div className="text-xs text-zinc-400">1:{bt.odds}</div>
                </button>
              ))}
            </div>
            {currentBetType && (
              <p className="mt-2 text-xs text-zinc-500">{currentBetType.description}</p>
            )}
          </div>

          <div>
            <label className="label">
              Số đánh{" "}
              {currentBetType && (
                <span className="text-zinc-500">
                  ({currentBetType.min_numbers}-{currentBetType.max_numbers} số, cách nhau dấu cách hoặc dấu phẩy)
                </span>
              )}
            </label>
            <input
              className="input font-mono"
              value={numbers}
              onChange={(e) => setNumbers(e.target.value)}
              placeholder="VD: 23 45 67"
              required
            />
            {parsedNumbers.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {parsedNumbers.map((n, i) => (
                  <span key={i} className="badge badge-yellow font-mono">
                    {n}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Tiền/điểm (VND)</label>
              <input
                type="number"
                className="input"
                value={stake}
                min={1000}
                step={1000}
                onChange={(e) => setStake(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="label">Số điểm</label>
              <input
                type="number"
                className="input"
                value={points}
                min={1}
                max={100}
                onChange={(e) => setPoints(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 p-3 text-sm">
            <Row label="Tổng cược" value={formatVND(totalStake)} />
            <Row label="Có thể thắng (tối đa)" value={formatVND(potential)} highlight />
            {user && <Row label="Số dư hiện tại" value={formatVND(user.balance)} />}
          </div>

          {submitMsg && (
            <div
              className={`rounded-md border p-3 text-sm ${
                submitMsg.ok
                  ? "border-emerald-800 bg-emerald-900/30 text-emerald-300"
                  : "border-red-800 bg-red-900/30 text-red-300"
              }`}
            >
              {submitMsg.text}
            </div>
          )}

          <button
            type="submit"
            className="btn-primary w-full"
            disabled={submitting || (status ? !status.is_open : false) || !currentBetType}
          >
            {submitting
              ? "Đang đặt cược..."
              : !hydrated
                ? "Đang tải..."
                : !user
                  ? "Đăng nhập để đặt cược"
                  : status && !status.is_open
                    ? "Đã hết giờ cược"
                    : "Đặt cược"}
          </button>
        </form>
      </div>

      <aside className="space-y-4">
        <div className="card">
          <h3 className="font-semibold">Tỉ lệ trả thưởng</h3>
          <ul className="mt-3 space-y-2 text-sm">
            {game.bet_types.map((bt) => (
              <li key={bt.type_id} className="flex items-center justify-between">
                <span className="text-zinc-300">{bt.display_name}</span>
                <span className="font-mono text-gold">1:{bt.odds}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card text-xs text-zinc-400">
          <h3 className="text-sm font-semibold text-zinc-200">Quy tắc</h3>
          <ul className="mt-2 list-disc space-y-1 pl-4">
            <li>Cutoff {game.cutoff_time}: sau giờ này không thể đặt cược.</li>
            <li>Kết quả {game.result_time}: hệ thống tự lấy và tính tiền.</li>
            <li>Lô: tính theo số lần số xuất hiện (có duplicate).</li>
            <li>Đề: chỉ so với 2 số cuối Giải Đặc Biệt.</li>
          </ul>
        </div>
      </aside>
    </div>
  );
}

function Row({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-zinc-400">{label}</span>
      <span className={`font-mono ${highlight ? "text-gold font-semibold" : "text-zinc-100"}`}>{value}</span>
    </div>
  );
}
