"use client";
import { Suspense } from "react";
import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { useAccount } from "wagmi";
import { getUser, getPoints, getUserNodes, getChainNodes, UserInfo, NodeInfo, ChainNodeInfo, PointsInfo } from "../../lib/api";
import { NodeCard } from "../../components/NodeCard";

function DashboardContent() {
  const params = useSearchParams();
  const router = useRouter();
  const { address } = useAccount();
  const username = params.get("username") || "";

  const [user, setUser] = useState<UserInfo | null>(null);
  const [points, setPoints] = useState<PointsInfo | null>(null);
  const [nodes, setNodes] = useState<NodeInfo[]>([]);
  const [chainMap, setChainMap] = useState<Record<string, ChainNodeInfo[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!username) { router.push("/"); return; }
    load();
    const interval = setInterval(load, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, [username]);

  async function load() {
    try {
      const [u, p, n] = await Promise.all([
        getUser(username),
        getPoints(username),
        getUserNodes(username),
      ]);
      if (!u) { setError("User not found"); setLoading(false); return; }
      setUser(u);
      setPoints(p);
      setNodes(n);

      // Load chain nodes for each node
      const map: Record<string, ChainNodeInfo[]> = {};
      await Promise.all(n.map(async node => {
        map[node.node_id] = await getChainNodes(node.node_id);
      }));
      setChainMap(map);
    } catch {
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  const activeNodes = nodes.filter(n => n.status === "active").length;
  const totalChainNodes = Object.values(chainMap).flat().filter(c => c.status === "active").length;

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-gray-400">Loading...</div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="text-nexora-red mb-4">{error}</div>
        <button onClick={() => router.push("/")} className="text-nexora-accent hover:underline">← Back</button>
      </div>
    </div>
  );

  return (
    <main className="min-h-screen">
      {/* Nav */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-nexora-border">
        <button onClick={() => router.push("/")} className="text-xl font-bold text-nexora-accent">Nexora</button>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">{username}</span>
          <ConnectButton />
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Wallet link banner */}
        {!user?.wallet_address && address && (
          <div className="bg-nexora-yellow/10 border border-nexora-yellow/30 rounded-xl p-4 mb-6 flex items-center justify-between">
            <div>
              <div className="font-semibold text-nexora-yellow">Wallet not linked</div>
              <div className="text-sm text-gray-400">Your wallet is connected but not linked to this account yet.</div>
            </div>
            <button
              onClick={async () => {
                if (!address) return;
                try {
                  const { linkWallet } = await import("@/lib/api");
                  await linkWallet(username, address);
                  load();
                } catch (e: any) { alert(e.message); }
              }}
              className="bg-nexora-yellow text-black font-semibold px-4 py-2 rounded-lg text-sm hover:opacity-90"
            >
              Link Wallet
            </button>
          </div>
        )}

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Available Points", value: points?.points.toFixed(2) || "0", color: "text-nexora-accent" },
            { label: "Total Earned", value: points?.total_earned.toFixed(2) || "0", color: "text-white" },
            { label: "Active Nodes", value: activeNodes.toString(), color: "text-nexora-green" },
            { label: "Chain Nodes", value: totalChainNodes.toString(), color: "text-nexora-yellow" },
          ].map(s => (
            <div key={s.label} className="bg-nexora-card border border-nexora-border rounded-xl p-4">
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-gray-400 text-sm mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Wallet info */}
        <div className="bg-nexora-card border border-nexora-border rounded-xl p-4 mb-8">
          <div className="text-sm text-gray-400 mb-1">Linked Wallet</div>
          {user?.wallet_address ? (
            <div className="font-mono text-nexora-green">{user.wallet_address}</div>
          ) : (
            <div className="text-gray-500">No wallet linked — connect MetaMask above to link</div>
          )}
        </div>

        {/* Nodes */}
        <div>
          <h2 className="text-lg font-semibold mb-4">
            Nodes <span className="text-gray-500 font-normal text-sm">({nodes.length})</span>
          </h2>
          {nodes.length === 0 ? (
            <div className="bg-nexora-card border border-nexora-border rounded-xl p-8 text-center text-gray-500">
              No nodes found. Run <code className="text-nexora-accent">python cli/main.py start</code> to start a node.
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {nodes.map(node => (
                <NodeCard key={node.node_id} node={node} chains={chainMap[node.node_id] || []} />
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-gray-400">Loading...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
