"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/store";

export function Protected({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const user = useAuth((s) => s.user);
  const hydrated = useAuth((s) => s.hydrated);

  useEffect(() => {
    if (hydrated && !user) {
      router.replace("/login");
    }
  }, [hydrated, user, router]);

  if (!hydrated) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-zinc-500">
        Đang tải...
      </div>
    );
  }
  if (!user) return null;
  return <>{children}</>;
}
