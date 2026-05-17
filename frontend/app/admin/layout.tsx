"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Banknote, Users, ArrowDownToLine } from "lucide-react";

import { AdminProtected } from "@/components/AdminProtected";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/admin", label: "Tổng quan", icon: LayoutDashboard, exact: true },
  { href: "/admin/deposits", label: "Lệnh nạp", icon: Banknote },
  { href: "/admin/withdrawals", label: "Lệnh rút", icon: ArrowDownToLine },
  { href: "/admin/users", label: "Người dùng", icon: Users },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <AdminProtected>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Quản trị Sicbo</h1>
          <span className="rounded-md bg-red-900/30 px-2 py-1 text-xs font-semibold uppercase text-red-300">
            Admin
          </span>
        </div>

        <nav className="flex flex-wrap gap-1 border-b border-zinc-800 pb-2">
          {tabs.map((t) => {
            const active = t.exact ? pathname === t.href : pathname.startsWith(t.href);
            const Icon = t.icon;
            return (
              <Link
                key={t.href}
                href={t.href}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition",
                  active
                    ? "bg-zinc-800 text-white"
                    : "text-zinc-400 hover:bg-zinc-900 hover:text-white",
                )}
              >
                <Icon className="h-4 w-4" />
                {t.label}
              </Link>
            );
          })}
        </nav>

        <div>{children}</div>
      </div>
    </AdminProtected>
  );
}
