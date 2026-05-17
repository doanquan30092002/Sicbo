"use client";

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";

import {
  AdminStats,
  Bet,
  BetList,
  CutoffStatus,
  Deposit,
  DepositInit,
  DepositList,
  Game,
  GameResult,
  LoginResponse,
  PlaceBetPayload,
  TelegramLinkToken,
  TokenPair,
  Transaction,
  TransactionList,
  User,
  UserList,
  Withdrawal,
  WithdrawalList,
} from "./types";

const ACCESS_KEY = "sicbo_access_token";
const REFRESH_KEY = "sicbo_refresh_token";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(tokens: TokenPair): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function tryRefresh(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  try {
    const res = await axios.post<TokenPair>(`${BASE_URL}/api/auth/refresh`, {
      refresh_token: refresh,
    });
    setTokens(res.data);
    return res.data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retried?: boolean })
      | undefined;
    if (
      error.response?.status === 401 &&
      original &&
      !original._retried &&
      !original.url?.includes("/api/auth/")
    ) {
      original._retried = true;
      if (!refreshing) refreshing = tryRefresh();
      const newAccess = await refreshing;
      refreshing = null;
      if (newAccess && original.headers) {
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api.request(original);
      }
    }
    return Promise.reject(error);
  },
);

export function extractApiError(err: unknown, fallback = "Đã có lỗi xảy ra"): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { detail?: unknown } | undefined;
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
      const first = data.detail[0] as { msg?: string };
      if (first?.msg) return first.msg;
    }
    if (err.message) return err.message;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}

// ---------- Auth ----------

export async function apiLogin(username: string, password: string): Promise<LoginResponse> {
  const res = await api.post<LoginResponse>("/api/auth/login", { username, password });
  return res.data;
}

export interface RegisterPayload {
  username: string;
  password: string;
  phone?: string;
  email?: string;
}

export async function apiRegister(payload: RegisterPayload): Promise<User> {
  const res = await api.post<User>("/api/auth/register", payload);
  return res.data;
}

export async function apiMe(): Promise<User> {
  const res = await api.get<User>("/api/auth/me");
  return res.data;
}

export async function apiTelegramLinkToken(): Promise<TelegramLinkToken> {
  const res = await api.post<TelegramLinkToken>("/api/auth/telegram/link-token");
  return res.data;
}

// ---------- Games ----------

export async function apiListGames(): Promise<Game[]> {
  const res = await api.get<Game[]>("/api/games");
  return res.data;
}

export async function apiCutoffStatus(gameId: string): Promise<CutoffStatus> {
  const res = await api.get<CutoffStatus>(`/api/games/${gameId}/cutoff-status`);
  return res.data;
}

// ---------- Bets ----------

export async function apiPlaceBet(payload: PlaceBetPayload): Promise<Bet> {
  const res = await api.post<Bet>("/api/bets", payload);
  return res.data;
}

export interface ListBetsParams {
  game_id?: string;
  draw_date?: string;
  status?: string;
  page?: number;
  limit?: number;
}

export async function apiListBets(params: ListBetsParams = {}): Promise<BetList> {
  const res = await api.get<BetList>("/api/bets", { params });
  return res.data;
}

export async function apiCancelBet(betId: number): Promise<Bet> {
  const res = await api.delete<Bet>(`/api/bets/${betId}`);
  return res.data;
}

// ---------- Wallet ----------

export interface DepositInitPayload {
  amount: number | string;
  payment_method?: "bank_transfer" | "momo";
}

export async function apiInitDeposit(payload: DepositInitPayload): Promise<DepositInit> {
  const res = await api.post<DepositInit>("/api/wallet/deposit/init", payload);
  return res.data;
}

export async function apiGetDeposit(depositId: number): Promise<DepositInit> {
  const res = await api.get<DepositInit>(`/api/wallet/deposits/${depositId}`);
  return res.data;
}

export interface WithdrawalPayload {
  amount: number | string;
  payment_method?: "bank_transfer" | "momo";
  account_number: string;
  account_name: string;
  bank_name?: string;
}

export async function apiRequestWithdrawal(payload: WithdrawalPayload): Promise<Withdrawal> {
  const res = await api.post<Withdrawal>("/api/wallet/withdraw", payload);
  return res.data;
}

export async function apiBalance(): Promise<{ user_id: number; balance: string }> {
  const res = await api.get<{ user_id: number; balance: string }>("/api/wallet/balance");
  return res.data;
}

export async function apiListTransactions(page = 1, limit = 20): Promise<TransactionList> {
  const res = await api.get<TransactionList>("/api/wallet/transactions", {
    params: { page, limit },
  });
  return res.data;
}

// ---------- Results ----------

export async function apiResultToday(gameId: string): Promise<GameResult> {
  const res = await api.get<GameResult>(`/api/results/${gameId}/today`);
  return res.data;
}

export async function apiResultRecent(gameId: string, limit = 7): Promise<{ items: GameResult[] }> {
  const res = await api.get<{ items: GameResult[] }>(`/api/results/${gameId}`, {
    params: { limit },
  });
  return res.data;
}

// ---------- Admin ----------

export async function apiAdminStats(): Promise<AdminStats> {
  const res = await api.get<AdminStats>("/api/admin/stats");
  return res.data;
}

export async function apiAdminListPendingDeposits(page = 1, limit = 20): Promise<DepositList> {
  const res = await api.get<DepositList>("/api/admin/deposits/pending", {
    params: { page, limit },
  });
  return res.data;
}

export async function apiAdminConfirmDeposit(
  depositId: number,
  payload: { override_amount?: string; note?: string } = {},
): Promise<Deposit> {
  const res = await api.post<Deposit>(`/api/admin/deposits/${depositId}/confirm`, payload);
  return res.data;
}

export async function apiAdminCreditDirect(payload: {
  user_id: number;
  amount: string | number;
  note?: string;
}): Promise<Transaction> {
  const res = await api.post<Transaction>("/api/admin/deposits/credit", payload);
  return res.data;
}

export async function apiAdminListPendingWithdrawals(page = 1, limit = 20): Promise<WithdrawalList> {
  const res = await api.get<WithdrawalList>("/api/admin/withdrawals/pending", {
    params: { page, limit },
  });
  return res.data;
}

export async function apiAdminApproveWithdrawal(withdrawalId: number): Promise<Withdrawal> {
  const res = await api.post<Withdrawal>(`/api/admin/withdrawals/${withdrawalId}/approve`);
  return res.data;
}

export async function apiAdminRejectWithdrawal(
  withdrawalId: number,
  reason?: string,
): Promise<Withdrawal> {
  const res = await api.post<Withdrawal>(`/api/admin/withdrawals/${withdrawalId}/reject`, {
    reason,
  });
  return res.data;
}

export async function apiAdminListUsers(params: {
  search?: string;
  page?: number;
  limit?: number;
} = {}): Promise<UserList> {
  const res = await api.get<UserList>("/api/admin/users", { params });
  return res.data;
}
