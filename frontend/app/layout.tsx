import type { Metadata } from "next";

import "./globals.css";
import { AuthProvider } from "@/components/AuthProvider";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Sicbo - Nạp 1 phút rút 1 giây",
  description: "Web app cờ bạc số đề dựa trên kết quả XSMB.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <AuthProvider>
          <Navbar />
          <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
          <footer className="mx-auto max-w-6xl px-4 py-8 text-center text-xs text-zinc-600">
            © {new Date().getFullYear()} Sicbo — Chơi có trách nhiệm. Chỉ dành cho người 18+.
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
