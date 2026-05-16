# Frontend Developer Memory - Sicbo

## Ngữ cảnh
Bạn build frontend Sicbo: Next.js 14 App Router + TypeScript strict + Tailwind + shadcn/ui + Zustand. Deploy lên Vercel free tier.

## Trạng thái hiện tại
**Frontend CHƯA được tạo.** Chỉ có backend đang chạy. Khi bắt đầu Phase 6, cần:
1. `npx create-next-app@latest frontend --typescript --tailwind --app`
2. `cd frontend && npx shadcn-ui@latest init`
3. Cài: axios, zustand, swr, sonner (toast), react-hook-form, zod

## Cấu trúc dự kiến

```
frontend/
├── app/
│   ├── layout.tsx                    # Root layout + Toaster + AuthProvider
│   ├── page.tsx                      # Landing (redirect /login or /dashboard)
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (dashboard)/
│       ├── layout.tsx                # Auth guard (redirect /login if no token)
│       ├── dashboard/page.tsx        # Balance + today's bets summary
│       ├── bet/page.tsx              # Đặt cược (form + cutoff countdown)
│       ├── results/page.tsx          # Kết quả XSMB hôm nay
│       ├── history/page.tsx          # Lịch sử cược
│       ├── wallet/
│       │   ├── deposit/page.tsx      # Nạp tiền (VietQR)
│       │   └── withdraw/page.tsx     # Rút tiền form
│       └── admin/                    # Admin pages (is_admin only)
├── components/
│   ├── ui/                           # shadcn primitives
│   ├── layout/                       # Header, Sidebar, BottomNav (mobile)
│   ├── bet/                          # BetForm, BetCard, BetStatusBadge
│   ├── wallet/                       # DepositQR, WithdrawForm
│   └── results/                      # LotteryNumbers, ResultCard
├── lib/
│   ├── api.ts                        # Axios instance + JWT interceptor + refresh logic
│   ├── auth.ts                       # localStorage token helpers
│   └── utils.ts                      # formatMoney, formatDate, classnames
├── store/
│   └── auth.ts                       # Zustand persist (user, tokens)
├── types/
│   └── api.ts                        # Types từ Pydantic schemas backend
└── hooks/
    ├── useBalance.ts                 # SWR /api/wallet/balance
    ├── useBets.ts                    # SWR /api/bets
    ├── useGames.ts                   # SWR /api/games (cached lâu)
    └── useCutoffCountdown.ts         # Đếm ngược tới 18:10 VN time
```

## API Client (lib/api.ts) - quan trọng

```typescript
const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL });

api.interceptors.request.use((c) => {
  const t = localStorage.getItem('access_token');
  if (t) c.headers.Authorization = `Bearer ${t}`;
  return c;
});

api.interceptors.response.use(
  (r) => r,
  async (err) => {
    if (err.response?.status === 401 && !err.config._retry) {
      err.config._retry = true;
      const rt = localStorage.getItem('refresh_token');
      const { data } = await axios.post(`${baseURL}/api/auth/refresh`, { refresh_token: rt });
      localStorage.setItem('access_token', data.access_token);
      err.config.headers.Authorization = `Bearer ${data.access_token}`;
      return axios(err.config);
    }
    return Promise.reject(err);
  }
);
```

## Cutoff Countdown (UI ONLY)

```typescript
// 18:10 VN time — KHÔNG security check, chỉ UX
// Server enforce cutoff trong PlaceBet use case
export function useCutoffCountdown() {
  // returns { seconds, isClosed, displayString }
}
```

## Format tiền (Việt)

```typescript
export const formatMoney = (amount: number | string) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(Number(amount));
// "100.000 ₫"
```

## Backend API endpoints (đã có)

| Action | Method + Path |
|---|---|
| Register | POST /api/auth/register |
| Login | POST /api/auth/login → access+refresh tokens |
| Refresh | POST /api/auth/refresh |
| Get me | GET /api/auth/me |
| Telegram link | POST /api/auth/telegram/link-token → 6-digit code |
| List games | GET /api/games |
| Cutoff status | GET /api/games/xsmb/cutoff-status |
| Place bet | POST /api/bets |
| My bets | GET /api/bets?page=1&limit=20 |
| Bet detail | GET /api/bets/{id} |
| Balance | GET /api/wallet/balance |
| Deposit init | POST /api/wallet/deposit/init → VietQR URL |
| Withdraw | POST /api/wallet/withdraw |
| Transactions | GET /api/wallet/transactions |
| XSMB result today | GET /api/results/xsmb/today |

## Quy tắc quan trọng

- **TypeScript strict** — noImplicitAny, strictNullChecks
- **Server Components mặc định**, `"use client"` chỉ khi cần hooks/events
- **Mobile-first**: BottomNav mobile, Sidebar desktop, breakpoint md:
- **Decimal từ API về dạng string** — luôn `Number()` hoặc `parseFloat()`
- **shadcn/ui**: Button, Input, Card, Dialog, Badge, Table, Toast, Form
- **Loading states**: dùng `Skeleton` từ shadcn cho data fetching
- **Error boundary** trong (dashboard)/layout.tsx

## ENV vars

```env
NEXT_PUBLIC_API_URL=http://localhost:8000      # dev
NEXT_PUBLIC_API_URL=https://api.sicbo.app      # prod
NEXT_PUBLIC_APP_NAME=Sicbo
```

## Lệnh dev

```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000
npm run build && npm start    # test prod build
```

Xem `.claude/agent-memory/default/MEMORY.md` để biết state dự án đầy đủ.
