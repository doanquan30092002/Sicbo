"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Wallet, User, Dice5, History, Trophy, Shield } from "lucide-react";

import { useAuth } from "@/lib/store";
import { formatVND, cn } from "@/lib/utils";

const navLinks = [
  { href: "/", label: "Trang chủ", icon: Dice5 },
  { href: "/games", label: "Đặt cược", icon: Trophy },
  { href: "/history", label: "Lịch sử", icon: History },
  { href: "/wallet", label: "Ví", icon: Wallet },
];

export function Navbar() {
  const user = useAuth((s) => s.user);
  const signOut = useAuth((s) => s.signOut);
  const router = useRouter();
  const pathname = usePathname();

  const handleSignOut = () => {
    signOut();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <Dice5 className="h-6 w-6 text-brand" />
          <span className="text-lg font-bold tracking-wide">
            <span className="text-brand">SIC</span>
            <span className="text-gold">BO</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {navLinks.map((l) => {
            const active = pathname === l.href || pathname.startsWith(l.href + "/");
            const Icon = l.icon;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition",
                  active ? "bg-zinc-800 text-white" : "text-zinc-400 hover:bg-zinc-900 hover:text-white",
                )}
              >
                <Icon className="h-4 w-4" />
                {l.label}
              </Link>
            );
          })}
          {user?.is_admin && (
            <Link
              href="/admin"
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition",
                pathname.startsWith("/admin")
                  ? "bg-red-900/40 text-red-200"
                  : "text-red-400 hover:bg-red-900/30 hover:text-red-200",
              )}
            >
              <Shield className="h-4 w-4" />
              Admin
            </Link>
          )}
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Link
                href="/wallet"
                className="hidden rounded-lg border border-gold/40 bg-gold/10 px-3 py-1 text-sm font-semibold text-gold hover:bg-gold/20 sm:block"
              >
                {formatVND(user.balance)}
              </Link>
              <Link href="/profile" className="flex items-center gap-1.5 text-sm text-zinc-300 hover:text-white">
                <User className="h-4 w-4" />
                <span className="hidden sm:inline">{user.username}</span>
              </Link>
              <button onClick={handleSignOut} className="btn-ghost px-2 py-1" title="Đăng xuất">
                <LogOut className="h-4 w-4" />
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn-secondary">
                Đăng nhập
              </Link>
              <Link href="/register" className="btn-primary hidden sm:inline-flex">
                Đăng ký
              </Link>
            </>
          )}
        </div>
      </div>

      <nav className="flex items-center justify-around border-t border-zinc-900 px-1 py-1 md:hidden">
        {navLinks.map((l) => {
          const active = pathname === l.href || pathname.startsWith(l.href + "/");
          const Icon = l.icon;
          return (
            <Link
              key={l.href}
              href={l.href}
              className={cn(
                "flex flex-col items-center gap-0.5 rounded px-3 py-1 text-[11px]",
                active ? "text-brand" : "text-zinc-400",
              )}
            >
              <Icon className="h-5 w-5" />
              {l.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
