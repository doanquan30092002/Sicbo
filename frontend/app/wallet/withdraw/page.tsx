"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { apiRequestWithdrawal, extractApiError } from "@/lib/api";
import { Withdrawal } from "@/lib/types";
import { Protected } from "@/components/Protected";
import { useAuth } from "@/lib/store";
import { formatVND } from "@/lib/utils";

export default function WithdrawPage() {
  return (
    <Protected>
      <WithdrawInner />
    </Protected>
  );
}

function WithdrawInner() {
  const user = useAuth((s) => s.user);
  const [amount, setAmount] = useState("100000");
  const [method, setMethod] = useState<"bank_transfer" | "momo">("bank_transfer");
  const [accountNumber, setAccountNumber] = useState("");
  const [accountName, setAccountName] = useState("");
  const [bankName, setBankName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<Withdrawal | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const w = await apiRequestWithdrawal({
        amount: Number(amount),
        payment_method: method,
        account_number: accountNumber.trim(),
        account_name: accountName.trim(),
        bank_name: bankName.trim() || undefined,
      });
      setSuccess(w);
    } catch (err) {
      setError(extractApiError(err, "Không tạo được lệnh rút"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold">Rút tiền</h1>
      <p className="mt-1 text-sm text-zinc-400">
        Tối thiểu 50,000 VND. Admin sẽ duyệt thủ công trong vòng vài phút – vài giờ.
      </p>

      <div className="card mt-4 flex items-center justify-between">
        <div>
          <div className="text-xs text-zinc-500">Số dư khả dụng</div>
          <div className="text-2xl font-bold text-gold">
            {user ? formatVND(user.balance) : "—"}
          </div>
        </div>
        <Link href="/wallet" className="btn-ghost">← Về ví</Link>
      </div>

      {success ? (
        <div className="card mt-4 border-emerald-700 bg-emerald-900/20">
          <h2 className="text-lg font-semibold text-emerald-300">Đã gửi yêu cầu rút #{success.id}</h2>
          <ul className="mt-3 space-y-1 text-sm text-zinc-300">
            <li>Số tiền: <strong>{formatVND(success.amount)}</strong></li>
            <li>Phương thức: {success.payment_method}</li>
            <li>STK nhận: <span className="font-mono">{success.account_number}</span> — {success.account_name}</li>
            {success.bank_name && <li>Bank: {success.bank_name}</li>}
            <li>Trạng thái: <span className="badge badge-yellow">{success.status}</span></li>
          </ul>
          <p className="mt-3 text-xs text-zinc-500">
            Tiền đã bị trừ khỏi số dư. Nếu admin từ chối, số tiền sẽ được hoàn lại.
          </p>
        </div>
      ) : (
        <form onSubmit={submit} className="card mt-4 space-y-4">
          <div>
            <label className="label">Số tiền (VND)</label>
            <input
              type="number"
              className="input"
              value={amount}
              min={50000}
              step={1000}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label">Phương thức</label>
            <select
              className="input"
              value={method}
              onChange={(e) => setMethod(e.target.value as "bank_transfer" | "momo")}
            >
              <option value="bank_transfer">Chuyển khoản ngân hàng</option>
              <option value="momo">MoMo</option>
            </select>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="label">Số tài khoản / SĐT MoMo</label>
              <input
                className="input font-mono"
                value={accountNumber}
                onChange={(e) => setAccountNumber(e.target.value)}
                minLength={6}
                maxLength={30}
                required
              />
            </div>
            <div>
              <label className="label">Tên chủ tài khoản</label>
              <input
                className="input"
                value={accountName}
                onChange={(e) => setAccountName(e.target.value)}
                minLength={2}
                maxLength={100}
                required
              />
            </div>
          </div>
          {method === "bank_transfer" && (
            <div>
              <label className="label">Tên ngân hàng (tùy chọn)</label>
              <input
                className="input"
                value={bankName}
                onChange={(e) => setBankName(e.target.value)}
                placeholder="VD: VietinBank"
                maxLength={100}
              />
            </div>
          )}
          {error && (
            <div className="rounded-md border border-red-800 bg-red-900/30 p-3 text-sm text-red-300">
              {error}
            </div>
          )}
          <button type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Đang gửi yêu cầu..." : "Gửi yêu cầu rút"}
          </button>
        </form>
      )}
    </div>
  );
}
