"use client";
import { useState } from "react";
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
    <main className="min-h-screen flex flex-col">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-nexora-border">
        <span className="text-xl font-bold text-nexora-accent">Nexora</span>
        <ConnectButton />
      </nav>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 text-center gap-8">
        <div>
          <h1 className="text-5xl font-bold mb-4">
            Distributed.<br />
            <span className="text-nexora-accent">Verified.</span> Rewarded.
          </h1>
          <p className="text-gray-400 text-lg max-w-xl mx-auto">
            Run lightweight nodes, verify blockchain networks, and earn rewards.
            Connect your wallet to track your nodes and points.
          </p>
        </div>

        {/* Connect card */}
        <div className="bg-nexora-card border border-nexora-border rounded-2xl p-8 w-full max-w-md">
          <h2 className="text-lg font-semibold mb-6">View Your Dashboard</h2>

          <div className="mb-4">
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
                className="w-full bg-nexora-bg border border-nexora-border rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-nexora-accent mb-4"
              />
              {error && <p className="text-nexora-red text-sm mb-3">{error}</p>}
              <button
                onClick={handleConnect}
                disabled={loading}
                className="w-full bg-nexora-accent hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition"
              >
                {loading ? "Linking..." : "View Dashboard →"}
              </button>
            </>
          )}

          {!isConnected && (
            <p className="text-gray-500 text-sm mt-2">Connect your wallet to continue</p>
          )}
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-6 w-full max-w-2xl">
          {[
            { label: "Supported Chains", value: "8+" },
            { label: "Max Multiplier", value: "5×" },
            { label: "Points per Minute", value: "1 pt" },
          ].map(s => (
            <div key={s.label} className="bg-nexora-card border border-nexora-border rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-nexora-accent">{s.value}</div>
              <div className="text-gray-400 text-sm mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
