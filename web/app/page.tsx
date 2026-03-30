"use client";
import { useState } from "react";
import Image from "next/image";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { useAccount } from "wagmi";
import { useRouter } from "next/navigation";
import { linkWallet } from "../lib/api";

export default function Home() {
  const { address, isConnected } = useAccount();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleConnect() {
    if (!username.trim()) { setError("Enter your Nexora username"); return; }
    if (!address) { setError("Connect your wallet first"); return; }
    setLoading(true);
    setError("");
    try {
      await linkWallet(username.trim(), address);
      router.push(`/dashboard?username=${encodeURIComponent(username.trim())}`);
    } catch (e: any) {
      setError(e.message || "Failed to link wallet");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col bg-nexora-bg">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-nexora-border">
        <div className="flex items-center gap-3">
          <Image src="/logo.png" alt="Nexora" width={36} height={36} className="rounded-lg" />
          <span className="text-xl font-bold text-white tracking-tight">Nexora</span>
        </div>
        <ConnectButton />
      </nav>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-16 text-center">

        {/* Logo large */}
        <div className="mb-8">
          <Image src="/logo.png" alt="Nexora" width={96} height={96} className="rounded-2xl mx-auto shadow-lg shadow-nexora-accent/20" />
        </div>

        <h1 className="text-5xl md:text-6xl font-bold mb-4 leading-tight">
          Distributed.<br />
          <span className="text-nexora-accent">Verified.</span> Rewarded.
        </h1>
        <p className="text-gray-400 text-lg max-w-lg mx-auto mb-12">
          Run lightweight nodes, verify blockchain networks, and earn rewards.
          Connect your wallet to track your nodes and points.
        </p>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4 w-full max-w-lg mb-12">
          {[
            { label: "Supported Chains", value: "8+" },
            { label: "Max Multiplier", value: "5×" },
            { label: "Points / Minute", value: "1 pt" },
          ].map(s => (
            <div key={s.label} className="bg-nexora-card border border-nexora-border rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-nexora-accent">{s.value}</div>
              <div className="text-gray-500 text-xs mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Connect card */}
        <div className="bg-nexora-card border border-nexora-border rounded-2xl p-8 w-full max-w-md shadow-xl">
          <h2 className="text-lg font-semibold mb-2">View Your Dashboard</h2>
          <p className="text-gray-500 text-sm mb-6">Connect your wallet and enter your username to see your nodes and earnings.</p>

          <div className="mb-5 flex justify-center">
            <ConnectButton />
          </div>

          {isConnected && (
            <>
              <input
                type="text"
                placeholder="Your Nexora username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleConnect()}
                className="w-full bg-nexora-bg border border-nexora-border rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-nexora-accent mb-3 text-sm"
              />
              {error && <p className="text-nexora-red text-xs mb-3">{error}</p>}
              <button
                onClick={handleConnect}
                disabled={loading}
                className="w-full bg-nexora-accent hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition text-sm"
              >
                {loading ? "Linking..." : "View Dashboard →"}
              </button>
            </>
          )}

          {!isConnected && (
            <p className="text-gray-600 text-xs text-center mt-2">Connect your wallet above to continue</p>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-nexora-border px-8 py-4 flex items-center justify-between text-gray-600 text-xs">
        <div className="flex items-center gap-2">
          <Image src="/logo.png" alt="Nexora" width={16} height={16} className="rounded opacity-50" />
          <span>Nexora Node Network</span>
        </div>
        <span>Distributed. Verified. Rewarded.</span>
      </footer>
    </main>
  );
}
