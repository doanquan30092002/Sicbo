"use client";

import { useEffect } from "react";

import { apiMe, getAccessToken } from "@/lib/api";
import { useAuth } from "@/lib/store";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const setUser = useAuth((s) => s.setUser);
  const setHydrated = useAuth((s) => s.setHydrated);

  useEffect(() => {
    let mounted = true;
    async function init() {
      if (!getAccessToken()) {
        if (mounted) setHydrated(true);
        return;
      }
      try {
        const user = await apiMe();
        if (mounted) setUser(user);
      } catch {
        // token invalid - keep null
      } finally {
        if (mounted) setHydrated(true);
      }
    }
    init();
    return () => {
      mounted = false;
    };
  }, [setUser, setHydrated]);

  return <>{children}</>;
}
