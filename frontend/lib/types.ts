export interface User {
  id: number;
  username: string;
  balance: string;
  is_active: boolean;
  is_admin: boolean;
  phone?: string | null;
  email?: string | null;
  telegram_id?: number | null;
  telegram_username?: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginResponse {
  user: User;
  tokens: TokenPair;
}

export interface BetType {
  type_id: string;
  display_name: string;
  odds: string;
  min_numbers: number;
  max_numbers: number;
  description: string;
}

export interface Game {
  game_id: string;
  game_name: string;
  cutoff_time: string;
  result_time: string;
  is_active: boolean;
  bet_types: BetType[];
}

export interface CutoffStatus {
  game_id: string;
  is_open: boolean;
  cutoff_time: string;
  server_time: string;
  seconds_until_cutoff: number;
}

export interface Bet {
  id: number;
  user_id: number;
  game_id: string;
  draw_date: string;
  bet_type_id: string;
  numbers: string[];
  stake_per_point: string;
  points: number;
  total_stake: string;
  potential_win: string;
  status: "pending" | "won" | "lost" | "cancelled" | string;
  win_amount: string;
  source: string;
  placed_at: string;
  settled_at?: string | null;
}

export interface BetList {
  items: Bet[];
  total: number;
  page: number;
  limit: number;
}

export interface PlaceBetPayload {
  game_id: string;
  bet_type_id: string;
  numbers: string[];
  stake_per_point: string | number;
  points: number;
}

export interface DepositInit {
  deposit_id: number;
  amount: string;
  payment_method: string;
  transfer_content: string;
  bank_account?: string | null;
  bank_name?: string | null;
  bank_account_name?: string | null;
  qr_url?: string | null;
  status: string;
  created_at: string;
}

export interface Withdrawal {
  id: number;
  user_id: number;
  amount: string;
  payment_method: string;
  account_number: string;
  account_name: string;
  bank_name?: string | null;
  status: string;
  admin_note?: string | null;
  processed_by?: number | null;
  processed_at?: string | null;
  requested_at: string;
}

export interface Transaction {
  id: number;
  user_id: number;
  type: string;
  amount: string;
  balance_before: string;
  balance_after: string;
  status: string;
  reference_id?: string | null;
  description?: string | null;
  related_bet_id?: number | null;
  created_at: string;
}

export interface TransactionList {
  items: Transaction[];
  total: number;
  page: number;
  limit: number;
}

export interface GameResult {
  id: number;
  game_id: string;
  draw_date: string;
  parsed_data: Record<string, unknown>;
  fetched_at: string;
}

export interface TelegramLinkToken {
  token: string;
  expires_at: string;
}
