---
name: frontend-dev
description: Agent chuyên phát triển Next.js 14 frontend cho Sicbo (App Router + Tailwind + shadcn/ui + Zustand). Dùng khi cần tạo pages, components, API client, hoặc auth flow phía client.
---

# Frontend Developer Agent

## Context
Frontend Sicbo dùng Next.js 14 App Router, TypeScript strict, Tailwind CSS, shadcn/ui components, Zustand cho auth state. Deploy trên Vercel.

## Cấu trúc dự án frontend

```
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # Root layout (providers, fonts)
│   ├── page.tsx                  # Landing / redirect
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx            # Auth guard, sidebar
│   │   ├── dashboard/page.tsx    # Balance, today's bets summary
│   │   ├── bet/page.tsx          # Đặt cược form
│   │   ├── results/page.tsx      # Kết quả XSMB
│   │   ├── history/page.tsx      # Lịch sử cược
│   │   └── wallet/
│   │       ├── deposit/page.tsx
│   │       └── withdraw/page.tsx
│   └── api/                      # Route handlers (nếu cần proxy)
├── components/
│   ├── ui/                       # shadcn/ui primitives
│   ├── layout/                   # Sidebar, Header, BottomNav
│   ├── bet/                      # BetForm, BetCard, BetStatusBadge
│   ├── wallet/                   # DepositModal, QRCode, WithdrawForm
│   └── results/                  # ResultCard, LotteryNumbers
├── lib/
│   ├── api.ts                    # Axios instance với JWT interceptor
│   ├── auth.ts                   # Token storage helpers
│   └── utils.ts                  # formatMoney, formatDate, etc.
├── store/
│   └── auth.ts                   # Zustand auth store
├── types/
│   └── api.ts                    # TypeScript types từ backend schemas
└── hooks/
    ├── useBalance.ts             # SWR hook cho /api/wallet/balance
    ├── useBets.ts                # SWR hook cho /api/bets
    └── useCutoffCountdown.ts     # Countdown đến 18:10
```

## API Client (lib/api.ts)

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10000,
});

// Request interceptor: attach JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    if (err.response?.status === 401) {
      // Thử refresh token
      try {
        const { data } = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/refresh`, {
          refresh_token: localStorage.getItem('refresh_token'),
        });
        localStorage.setItem('access_token', data.access_token);
        err.config.headers.Authorization = `Bearer ${data.access_token}`;
        return axios(err.config);
      } catch {
        // Refresh failed → logout
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }
    return Promise.reject(err);
  }
);

export default api;
```

## Auth Store (Zustand)

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (tokens: Tokens, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null, accessToken: null, refreshToken: null,
      isAuthenticated: false,
      login: (tokens, user) => set({ ...tokens, user, isAuthenticated: true }),
      logout: () => set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false }),
    }),
    { name: 'sicbo-auth' }
  )
);
```

## Cutoff Countdown (hooks/useCutoffCountdown.ts)

```typescript
// UI-only: đếm ngược đến 18:10 VN time
// KHÔNG trust cho security — server enforce cutoff
export function useCutoffCountdown() {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      const cutoff = new Date();
      cutoff.setHours(18, 10, 0, 0);
      const diff = Math.max(0, (cutoff.getTime() - now.getTime()) / 1000);
      setSeconds(Math.floor(diff));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return seconds;
}
```

## Format tiền

```typescript
export const formatMoney = (amount: number | string) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(Number(amount));
// Kết quả: "100.000 ₫"
```

## Quy tắc quan trọng

1. **TypeScript strict mode** — `noImplicitAny`, `strictNullChecks`
2. **Server Components by default** — chỉ dùng `"use client"` khi cần (hooks, events)
3. **Cutoff là UI-only** — chỉ để UX, KHÔNG làm security check phía client
4. **SWR** cho data fetching với auto-revalidation
5. **shadcn/ui** cho components: Button, Input, Card, Badge, Dialog, Table
6. **Mobile-first** — BottomNav cho mobile, Sidebar cho desktop
7. **Decimal numbers** từ API trả về dạng string — dùng `parseFloat()` hoặc `Number()`

## Backend API endpoints

| Action | Method + Path |
|---|---|
| Login | `POST /api/auth/login` |
| Register | `POST /api/auth/register` |
| Get me | `GET /api/auth/me` |
| List games | `GET /api/games` |
| Place bet | `POST /api/bets` |
| My bets | `GET /api/bets?page=1` |
| Balance | `GET /api/wallet/balance` |
| Deposit init | `POST /api/wallet/deposit/init` |
| Withdraw | `POST /api/wallet/withdraw` |
| XSMB result | `GET /api/results/xsmb/today` |
| Cutoff status | `GET /api/games/xsmb/cutoff-status` |

## Environment variables

```env
NEXT_PUBLIC_API_URL=https://api.sicbo.app    # hoặc http://localhost:8000 cho dev
NEXT_PUBLIC_APP_NAME=Sicbo
```
