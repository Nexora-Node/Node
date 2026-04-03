"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getExplorerNodes, getNetworkStats, getMiningInfo, formatUptime, timeAgo, ExplorerNode, NetworkStats, MiningInfo } from "../../lib/api";

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 80 ? "text-nexora-green" : score >= 50 ? "text-nexora-yellow" : "text-nexora-red";
  return <span className={`font-mono text-sm ${color}`}>{score}/100</span>;
}

export default function Explorer() {
  const router = useRouter();
  const [nodes, setNodes] = useState<ExplorerNode[]>([]);
  const [stats, setStats] = useState<NetworkStats | null>(null);
  const [mining, setMining] = useState<MiningInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  async function load() {
    const [n, s, m] = await Promise.all([
      getExplorerNodes(),
      getNetworkStats(),
      getMiningInfo(),
    ]);
    setNodes(n);
    setStats(s);
    setMining(m);
    setLoading(false);
  }

  const filtered = nodes.filter(n =>
    n.username.toLowerCase().includes(search.toLowerCase()) ||
    n.node_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <main className="min-h-screen">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-nexora-border">
        <button onClick={() => router.push("/")} className="flex items-center gap-2 hover:opacity-80 transition">
          <img src="/logo.png" alt="Nexora" className="w-8 h-8 rounded-lg" />
          <span className="text-lg font-bold text-white">Nexora</span>
        </button>
        <span className="text-nexora-accent font-semibold text-sm">Network Explorer</span>
      </nav>

      <div className="max-w-6xl mx-auto px-4 py-8">

        {/* Network Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Active Nodes",    value: stats?.active_nodes.toString() ?? "—",                    color: "text-nexora-green"  },
            { label: "Total Users",     value: stats?.total_users.toString() ?? "—",                     color: "text-white"         },
            { label: "Mining Rate",     value: mining ? `${mining.current_rate_per_min.toFixed(6)}` : "—", color: "text-nexora-accent" },
            { label: "Uptime (hrs)",    value: stats?.total_uptime_hours.toFixed(1) ?? "—",              color: "text-nexora-yellow" },
          ].map(s => (
            <div key={s.label} className="bg-nexora-card border border-nexora-border rounded-xl p-4">
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-gray-400 text-sm mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Mining info bar */}
        {mining && (
          <div className="bg-nexora-card border border-nexora-border rounded-xl p-4 mb-6 flex flex-wrap gap-6 text-sm">
            <div><span className="text-gray-500">Epoch</span> <span className="text-white font-mono ml-2">#{mining.current_epoch}</span></div>
            <div><span className="text-gray-500">Next Decay</span> <span className="text-nexora-yellow font-mono ml-2">{mining.days_until_next_decay}d</span></div>
            <div><span className="text-gray-500">Distributed</span> <span className="text-white font-mono ml-2">{mining.total_distributed.toFixed(2)} / {mining.mining_supply_cap.toFixed(0)} NEXORA</span></div>
            <div><span className="text-gray-500">Remaining</span> <span className="text-nexora-green font-mono ml-2">{mining.remaining_supply.toFixed(2)} NEXORA</span></div>
          </div>
        )}

        {/* Search */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search by username or node ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full bg-nexora-card border border-nexora-border rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-nexora-accent"
          />
        </div>

        {/* Node Table */}
        <div className="bg-nexora-card border border-nexora-border rounded-xl overflow-hidden">
          <div className="grid grid-cols-5 gap-4 px-4 py-3 border-b border-nexora-border text-xs text-gray-500 uppercase tracking-wide">
            <div>Node ID</div>
            <div>User</div>
            <div>Uptime</div>
            <div>Last Seen</div>
            <div className="text-right">Score / IP</div>
          </div>

          {loading ? (
            <div className="px-4 py-8 text-center text-gray-500">Loading...</div>
          ) : filtered.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500">No active nodes found.</div>
          ) : (
            filtered.map((node, i) => (
              <div key={node.node_id} className={`grid grid-cols-5 gap-4 px-4 py-3 text-sm items-center ${i % 2 === 0 ? "" : "bg-nexora-bg/30"} hover:bg-nexora-border/20 transition`}>
                <div className="font-mono text-gray-300 truncate">{node.node_id}</div>
                <div className="text-nexora-accent font-medium truncate">{node.username}</div>
                <div className="text-white">{formatUptime(node.uptime)}</div>
                <div className="text-gray-400">{timeAgo(node.last_seen)}</div>
                <div className="text-right">
                  <ScoreBadge score={node.node_score} />
                  <div className="text-gray-600 text-xs font-mono mt-0.5">{node.ip_address}</div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="text-center text-gray-600 text-xs mt-4">
          {filtered.length} active node{filtered.length !== 1 ? "s" : ""} · refreshes every 30s · IP addresses are masked for privacy
        </div>
      </div>
    </main>
  );
}
