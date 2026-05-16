"use client";

import { FormEvent, useState } from "react";
import { Copy, Check } from "lucide-react";

import { apiInitDeposit, extractApiError } from "@/lib/api";
import { DepositInit } from "@/lib/types";
import { Protected } from "@/components/Protected";
import { formatVND } from "@/lib/utils";

export default function DepositPage() {
  return (
    <Protected>
      <DepositInner />
    </Protected>
  );
}

function DepositInner() {
  const [amount, setAmount] = useState<string>("100000");
  const [method, setMethod] = useState<"bank_transfer" | "momo">("bank_transfer");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deposit, setDeposit] = useState<DepositInit | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const d = await apiInitDeposit({ amount: Number(amount), payment_method: method });
      setDeposit(d);
    } catch (err) {
      setError(extractApiError(err, "Không tạo được lệnh nạp"));
    } finally {
      setLoading(false);
    }
  }

  const presets = [50000, 100000, 200000, 500000, 1000000, 2000000];

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div>
        <h1 className="text-2xl font-bold">Nạp tiền</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Chuyển khoản với đúng nội dung, hệ thống tự cộng tiền trong vài giây qua SePay.
        </p>
        <form onSubmit={submit} className="mt-5 card space-y-4">
          <div>
            <label className="label">Số tiền (VND)</label>
            <input
              type="number"
              className="input"
              value={amount}
              min={10000}
              step={1000}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
            <div className="mt-2 flex flex-wrap gap-2">
              {presets.map((p) => (
                <button
                  type="button"
                  key={p}
                  className="badge badge-gray hover:border-brand"
                  onClick={() => setAmount(String(p))}
                >
                  {formatVND(p)}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="label">Phương thức</label>
            <div className="grid grid-cols-2 gap-2">
              <MethodOption
                active={method === "bank_transfer"}
                onClick={() => setMethod("bank_transfer")}
                label="Chuyển khoản"
                desc="Quét VietQR hoặc bank app"
              />
              <MethodOption
                active={method === "momo"}
                onClick={() => setMethod("momo")}
                label="MoMo"
                desc="Số dư ví MoMo"
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
              {error}
            </div>
          )}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Đang tạo lệnh nạp..." : "Tạo lệnh nạp"}
          </button>
        </form>
      </div>

      <div>
        <h2 className="text-lg font-semibold">Hướng dẫn thanh toán</h2>
        {deposit ? (
          <div className="card mt-3 space-y-3">
            {deposit.qr_url && (
              <div className="flex justify-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={deposit.qr_url} alt="QR" className="h-72 w-72 rounded-md bg-white p-2" />
              </div>
            )}
            <CopyRow label="Ngân hàng" value={deposit.bank_name || "—"} />
            <CopyRow label="Số tài khoản" value={deposit.bank_account || "—"} />
            <CopyRow label="Tên người nhận" value={deposit.bank_account_name || "—"} />
            <CopyRow label="Số tiền" value={String(Number(deposit.amount))} display={formatVND(deposit.amount)} />
            <CopyRow label="Nội dung CK" value={deposit.transfer_content} highlight />
            <p className="text-xs text-zinc-500">
              ⚠️ Phải nhập đúng <strong className="text-yellow-300">{deposit.transfer_content}</strong> ở phần nội dung chuyển khoản. Sai nội dung sẽ KHÔNG tự cộng tiền.
            </p>
          </div>
        ) : (
          <div className="card mt-3 text-sm text-zinc-500">
            Tạo lệnh nạp ở bên trái để hiện QR và thông tin tài khoản.
          </div>
        )}
      </div>
    </div>
  );
}

function MethodOption({
  active,
  onClick,
  label,
  desc,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  desc: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md border px-3 py-2 text-left text-sm transition ${
        active
          ? "border-brand bg-brand/15 text-white"
          : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-zinc-500"
      }`}
    >
      <div className="font-medium">{label}</div>
      <div className="text-xs text-zinc-400">{desc}</div>
    </button>
  );
}

function CopyRow({
  label,
  value,
  display,
  highlight,
}: {
  label: string;
  value: string;
  display?: string;
  highlight?: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // ignore
    }
  };
  return (
    <div className="flex items-center justify-between gap-2 rounded-md border border-zinc-800 bg-zinc-950/40 px-3 py-2">
      <div className="min-w-0">
        <div className="text-xs text-zinc-500">{label}</div>
        <div
          className={`truncate font-mono ${highlight ? "text-yellow-300 font-bold" : "text-zinc-100"}`}
        >
          {display ?? value}
        </div>
      </div>
      <button onClick={handleCopy} className="btn-ghost shrink-0" title="Copy">
        {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
      </button>
    </div>
  );
}
