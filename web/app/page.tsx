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
        <div className="flex items-center gap-4">
          <a href="/explorer" className="text-gray-400 hover:text-nexora-accent text-sm transition">Explorer</a>
          <ConnectButton />
        </div>
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
      <footer className="border-t border-nexora-border px-8 py-5 flex flex-col md:flex-row items-center justify-between gap-4 text-gray-600 text-xs">
        <div className="flex items-center gap-2">
          <Image src="/logo.png" alt="Nexora" width={16} height={16} className="rounded opacity-50" />
          <span>Nexora Node Network</span>
        </div>
        <div className="flex items-center gap-6">
          <a href="https://x.com/nexoranode" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1.5 hover:text-white transition">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.737-8.835L1.254 2.25H8.08l4.253 5.622 5.911-5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
            Twitter
          </a>
          <a href="https://nexora-5.gitbook.io/nexora-docs" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1.5 hover:text-white transition">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M10.802 17.77a.703.703 0 1 1-.002 1.406.703.703 0 0 1 .002-1.406m11.024-4.347a.703.703 0 1 1 .001-1.406.703.703 0 0 1-.001 1.406m0-2.876a2.176 2.176 0 0 0-2.174 2.174c0 .233.039.465.115.691l-7.181 3.823a2.165 2.165 0 0 0-1.784-.937 2.176 2.176 0 0 0-2.174 2.174 2.176 2.176 0 0 0 2.174 2.174 2.176 2.176 0 0 0 2.174-2.174c0-.233-.039-.465-.115-.691l7.181-3.823a2.165 2.165 0 0 0 1.784.937 2.176 2.176 0 0 0 2.174-2.174 2.176 2.176 0 0 0-2.174-2.174"/>
            </svg>
            Docs
          </a>
          <a href="https://github.com/Nexora-Node/Node" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1.5 hover:text-white transition">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.02 10.02 0 0 0 22 12.017C22 6.484 17.522 2 12 2z"/>
            </svg>
            GitHub
          </a>
        </div>
      </footer>
    </main>
  );
}
