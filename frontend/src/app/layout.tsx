import type { Metadata } from "next";
import type { ReactNode } from "react";

import { QueryProvider } from "@/components/query-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "NeuroAgent — AI Agent Platform",
  description: "Give it a goal. Watch it think, plan, search, code, and deliver.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full bg-base antialiased">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
