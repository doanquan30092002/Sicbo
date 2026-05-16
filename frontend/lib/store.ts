"use client";

import { create } from "zustand";

import { User } from "./types";
import { clearTokens, setTokens } from "./api";
import { TokenPair } from "./types";

interface AuthState {
  user: User | null;
  hydrated: boolean;
  setUser: (user: User | null) => void;
  signIn: (user: User, tokens: TokenPair) => void;
  signOut: () => void;
  setHydrated: (v: boolean) => void;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  hydrated: false,
  setUser: (user) => set({ user }),
  signIn: (user, tokens) => {
    setTokens(tokens);
    set({ user });
  },
  signOut: () => {
    clearTokens();
    set({ user: null });
  },
  setHydrated: (v) => set({ hydrated: v }),
}));
