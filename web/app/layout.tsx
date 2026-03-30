import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Nexora — Distributed Node Network",
  description: "Run nodes, verify blockchain networks, earn rewards.",
  icons: { icon: "/logo.png" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-nexora-bg text-white min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
