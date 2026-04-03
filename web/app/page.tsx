"use client";
import Image from "next/image";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  return (
    <main className="min-h-screen flex flex-col bg-nexora-bg">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-nexora-border">
        <div className="flex items-center gap-3">
          <Image src="/logo.png" alt="Nexora" width={36} height={36} className="rounded-lg" />
          <span className="text-xl font-bold text-white tracking-tight">Nexora</span>
        </div>
        <div className="flex items-center gap-6 text-sm">
          <a href="/explorer" className="text-gray-400 hover:text-nexora-accent transition">Explorer</a>
          <a href="/dashboard" className="text-gray-400 hover:text-nexora-accent transition">Dashboard</a>
          <a href="https://nexora-5.gitbook.io/nexora-docs" target="_blank" rel="noopener noreferrer"
            className="text-gray-400 hover:text-nexora-accent transition">Docs</a>
          <a href="https://x.com/nexoranode" target="_blank" rel="noopener noreferrer"
            className="text-gray-400 hover:text-nexora-accent transition">Twitter</a>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center px-4 py-20 text-center">
        <div className="mb-8">
          <Image src="/logo.png" alt="Nexora" width={100} height={100} className="rounded-2xl mx-auto shadow-lg shadow-nexora-accent/20" />
        </div>
        <div className="inline-flex items-center gap-2 bg-nexora-card border border-nexora-border rounded-full px-4 py-1.5 text-xs text-nexora-accent mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-nexora-green animate-pulse inline-block" />
          Beta Live on Base Mainnet
        </div>
        <h1 className="text-5xl md:text-6xl font-bold mb-5 leading-tight tracking-tight">
          Mine <span className="text-nexora-accent">NEXORA</span><br />
          by running a node
        </h1>
        <p className="text-gray-400 text-lg max-w-xl mx-auto mb-10 leading-relaxed">
          Nexora is a distributed node network where participants earn <strong className="text-white">NEXORA</strong> tokens
          by running lightweight nodes that help verify the Base blockchain.
          No GPU. No heavy computation. Just run and earn.
        </p>
        <div className="flex flex-wrap gap-4 justify-center mb-16">
          <button
            onClick={() => router.push("/dashboard")}
            className="bg-nexora-accent hover:bg-indigo-500 text-white font-semibold px-8 py-3 rounded-xl transition text-sm"
          >
            Open Dashboard →
          </button>
          <a
            href="https://nexora-5.gitbook.io/nexora-docs"
            target="_blank" rel="noopener noreferrer"
            className="border border-nexora-border hover:border-nexora-accent text-gray-300 hover:text-white font-semibold px-8 py-3 rounded-xl transition text-sm"
          >
            Read Docs
          </a>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-3xl mb-20">
          {[
            { label: "Total Supply",      value: "240,000",   unit: "NEXORA"   },
            { label: "Mining Allocation", value: "200,000",   unit: "NEXORA"    },
            { label: "Starting Rate",     value: "0.2894",    unit: "NEXORA/min"},
            { label: "Decay Interval",    value: "24 days",   unit: "5% decay" },
          ].map(s => (
            <div key={s.label} className="bg-nexora-card border border-nexora-border rounded-xl p-5 text-center">
              <div className="text-2xl font-bold text-nexora-accent">{s.value}</div>
              <div className="text-gray-500 text-xs mt-1">{s.unit}</div>
              <div className="text-gray-600 text-xs mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>

        {/* How it works */}
        <div className="w-full max-w-3xl mb-20">
          <h2 className="text-2xl font-bold mb-8 text-white">How it works</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {[
              {
                step: "01",
                title: "Run a Node",
                desc: "Download the CLI, register with a referral code, and run python main.py start. Your node starts verifying the Base network.",
              },
              {
                step: "02",
                title: "Earn NEXORA",
                desc: "Every ~30 seconds your node sends a heartbeat. The backend validates activity and credits NEXORA to your account.",
              },
              {
                step: "03",
                title: "Claim On-Chain",
                desc: "Link your wallet in the dashboard and click Claim. NEXORA transfers directly to your wallet on Base Mainnet.",
              },
            ].map(s => (
              <div key={s.step} className="bg-nexora-card border border-nexora-border rounded-xl p-6 text-left">
                <div className="text-nexora-accent font-mono text-sm mb-3">{s.step}</div>
                <div className="font-semibold text-white mb-2">{s.title}</div>
                <div className="text-gray-500 text-sm leading-relaxed">{s.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Token info */}
        <div className="w-full max-w-3xl bg-nexora-card border border-nexora-border rounded-2xl p-6 text-left mb-20">
          <h2 className="text-lg font-bold text-white mb-4">Token</h2>
          <div className="grid md:grid-cols-2 gap-3 text-sm">
            {[
              ["Name",    "NEXORA NODE",           null],
              ["Symbol",  "NEXORA",                null],
              ["Network", "Base Mainnet",           null],
              ["Supply",  "240,000 NEXORA (fixed)", null],
            ].map(([k, v]) => (
              <div key={k as string} className="flex justify-between border-b border-nexora-border pb-2">
                <span className="text-gray-500">{k}</span>
                <span className="text-white font-mono text-xs">{v}</span>
              </div>
            ))}
            <div className="flex justify-between border-b border-nexora-border pb-2">
              <span className="text-gray-500">Contract</span>
              <a
                href="https://basescan.org/token/0xE0a4a9d3263ee93E167196954Ea4684418911E24"
                target="_blank" rel="noopener noreferrer"
                className="text-nexora-accent hover:underline font-mono text-xs"
              >
                0xE0a4a9d3...11E24 ↗
              </a>
            </div>
            <div className="flex justify-between border-b border-nexora-border pb-2">
              <span className="text-gray-500">Claim</span>
              <a
                href="https://basescan.org/address/0xaeD12935DA40EFf65d919CCc4b77Df185f4A2cf0#code"
                target="_blank" rel="noopener noreferrer"
                className="text-nexora-green hover:underline font-mono text-xs"
              >
                0xaeD12935...2cf0 ✓ ↗
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-nexora-border px-8 py-5 flex flex-col md:flex-row items-center justify-between gap-4 text-gray-600 text-xs">
        <div className="flex items-center gap-2">
          <Image src="/logo.png" alt="Nexora" width={16} height={16} className="rounded opacity-50" />
          <span>Nexora Node Network · Base Mainnet</span>
        </div>
        <div className="flex items-center gap-6">
          <a href="/explorer" className="hover:text-white transition">Explorer</a>
          <a href="https://x.com/nexoranode" target="_blank" rel="noopener noreferrer" className="hover:text-white transition">Twitter</a>
          <a href="https://nexora-5.gitbook.io/nexora-docs" target="_blank" rel="noopener noreferrer" className="hover:text-white transition">Docs</a>
          <a href="https://github.com/Nexora-Node/Node" target="_blank" rel="noopener noreferrer" className="hover:text-white transition">GitHub</a>
          <a href="https://basescan.org/token/0xE0a4a9d3263ee93E167196954Ea4684418911E24" target="_blank" rel="noopener noreferrer" className="hover:text-white transition">Basescan</a>
        </div>
      </footer>
    </main>
  );
}
