"use client";
import { Suspense } from "react";
import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { useAccount } from "wagmi";
import { getUser, getTokens, getUserNodes, getChainNodes, claimTokens, confirmClaim, getMiningInfo, UserInfo, NodeInfo, ChainNodeInfo, TokensInfo, MiningInfo } from "../../lib/api";
import { useWriteContract, useWaitForTransactionReceipt } from "wagmi";
import { NodeCard } from "../../components/NodeCard";

function DashboardContent() {
  const params = useSearchParams();
  const router = useRouter();
  const { address } = useAccount();
  const username = params.get("username") || "";

  const [user, setUser] = useState<UserInfo | null>(null);
  const [tokens, setTokens] = useState<TokensInfo | null>(null);
  const [miningInfo, setMiningInfo] = useState<MiningInfo | null>(null);
  const [nodes, setNodes] = useState<NodeInfo[]>([]);
  const [chainMap, setChainMap] = useState<Record<string, ChainNodeInfo[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [claiming, setClaiming] = useState(false);
  const [claimError, setClaimError] = useState("");

  // ClaimDistributor ABI (only the claim function)
  const DISTRIBUTOR_ABI = [
    {
      name: "claim",
      type: "function",
      stateMutability: "nonpayable",
      inputs: [
        { name: "amount",   type: "uint256" },
        { name: "nonce",    type: "uint256" },
        { name: "deadline", type: "uint256" },
        { name: "v",        type: "uint8"   },
        { name: "r",        type: "bytes32" },
        { name: "s",        type: "bytes32" },
      ],
      outputs: [],
    },
  ] as const;

  useEffect(() => {
    if (!username) {
      // No username — show connect prompt, don't redirect
      setLoading(false);
      return;
    }
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [username]);

  async function load() {
    try {
      const [u, t, n, m] = await Promise.all([
        getUser(username),
        getTokens(username),
        getUserNodes(username),
        getMiningInfo(),
      ]);
      if (!u) { setError("User not found"); setLoading(false); return; }
      setUser(u);
      setTokens(t);
      setNodes(n);
      setMiningInfo(m);

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

  const { writeContractAsync } = useWriteContract();

  async function handleClaim() {
    if (!tokens || tokens.tokens < 1) return;
    setClaiming(true);
    setClaimError("");
    try {
      // 1. Get signed voucher from backend
      const voucher = await claimTokens(username);

      // 2. Submit to ClaimDistributor contract (user pays gas)
      const txHash = await writeContractAsync({
        address: voucher.contract as `0x${string}`,
        abi: DISTRIBUTOR_ABI,
        functionName: "claim",
        args: [
          BigInt(voucher.amount),
          BigInt(voucher.nonce),
          BigInt(voucher.deadline),
          voucher.v,
          voucher.r as `0x${string}`,
          voucher.s as `0x${string}`,
        ],
        chainId: voucher.chain_id,
      });

      // 3. Confirm with backend to deduct DB balance
      await confirmClaim(username, txHash, voucher.pending_amount);
      await load();
    } catch (e: any) {
      setClaimError(e.shortMessage || e.message || "Claim failed");
    } finally {
      setClaiming(false);
    }
  }

  const activeNodes = nodes.filter(n => n.status === "active").length;
  const totalChainNodes = Object.values(chainMap).flat().filter(c => c.status === "active").length;

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-gray-400">Loading...</div>
    </div>
  );

  // No username — show connect prompt
  if (!username) return (
    <main className="min-h-screen flex flex-col">
      <nav className="flex items-center justify-between px-6 py-4 border-b border-nexora-border">
        <button onClick={() => router.push("/")} className="flex items-center gap-2 hover:opacity-80 transition">
          <img src="/logo.png" alt="Nexora" className="w-8 h-8 rounded-lg" />
          <span className="text-lg font-bold text-white">Nexora</span>
        </button>
        <ConnectButton />
      </nav>
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="bg-nexora-card border border-nexora-border rounded-2xl p-8 w-full max-w-md text-center">
          <img src="/logo.png" alt="Nexora" className="w-16 h-16 rounded-xl mx-auto mb-6 opacity-80" />
          <h2 className="text-xl font-bold text-white mb-2">Connect to Dashboard</h2>
          <p className="text-gray-500 text-sm mb-6">Enter your Nexora username to view your nodes and NEXORA balance.</p>
          <input
            type="text"
            placeholder="Your Nexora username"
            id="username-input"
            className="w-full bg-nexora-bg border border-nexora-border rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-nexora-accent mb-3 text-sm"
            onKeyDown={e => {
              if (e.key === "Enter") {
                const val = (e.target as HTMLInputElement).value.trim();
                if (val) router.push(`/dashboard?username=${encodeURIComponent(val)}`);
              }
            }}
          />
          <button
            onClick={() => {
              const val = (document.getElementById("username-input") as HTMLInputElement)?.value.trim();
              if (val) router.push(`/dashboard?username=${encodeURIComponent(val)}`);
            }}
            className="w-full bg-nexora-accent hover:bg-indigo-500 text-white font-semibold py-3 rounded-lg transition text-sm"
          >
            View Dashboard →
          </button>
        </div>
      </div>
    </main>
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
        <button onClick={() => router.push("/")} className="flex items-center gap-2 hover:opacity-80 transition">
          <img src="/logo.png" alt="Nexora" className="w-8 h-8 rounded-lg" />
          <span className="text-lg font-bold text-white">Nexora</span>
        </button>
        <div className="flex items-center gap-4">
          <a href="/explorer" className="text-gray-400 hover:text-nexora-accent text-sm transition hidden md:block">Explorer</a>
          <span className="text-gray-400 text-sm hidden md:block">{username}</span>
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
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[
            { label: "Available NEXORA", value: tokens?.tokens.toFixed(4) || "0", color: "text-nexora-accent" },
            { label: "Total Earned", value: tokens?.total_earned.toFixed(4) || "0", color: "text-white" },
            { label: "Active Nodes", value: activeNodes.toString(), color: "text-nexora-green" },
            { label: "Chain Nodes", value: totalChainNodes.toString(), color: "text-nexora-yellow" },
          ].map(s => (
            <div key={s.label} className="bg-nexora-card border border-nexora-border rounded-xl p-4">
              <div className={`text-2xl font-bold ${s.color}`}>{s.value}</div>
              <div className="text-gray-400 text-sm mt-1">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Mining rate info */}
        {miningInfo && (
          <div className="bg-nexora-card border border-nexora-border rounded-xl p-4 mb-6 flex flex-wrap gap-4 items-center justify-between">
            <div className="flex gap-6">
              <div>
                <div className="text-xs text-gray-500">Mining Rate</div>
                <div className="font-bold text-nexora-accent">
                  {miningInfo.current_rate_per_min.toFixed(6)} <span className="text-gray-400 font-normal text-xs">NEXORA/min</span>
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Epoch</div>
                <div className="font-bold text-white">#{miningInfo.current_epoch}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Next Decay</div>
                <div className="font-bold text-nexora-yellow">{miningInfo.days_until_next_decay}d</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Remaining Supply</div>
                <div className="font-bold text-white">
                  {miningInfo.remaining_supply.toFixed(0)} <span className="text-gray-400 font-normal text-xs">/ {miningInfo.mining_supply_cap.toFixed(0)}</span>
                </div>
              </div>
            </div>
            {miningInfo.supply_exhausted && (
              <div className="text-nexora-red text-sm font-semibold">Mining supply exhausted</div>
            )}
          </div>
        )}

        {/* Claim tokens panel */}
        <div className="bg-nexora-card border border-nexora-border rounded-xl p-4 mb-6 flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-400 mb-1">Claimed NEXORA</div>
            <div className="font-bold text-white">{tokens?.claimed_tokens.toFixed(4) || "0"} <span className="text-gray-500 text-xs font-normal">NEXORA</span></div>
            {tokens?.last_claim_at && (
              <div className="text-xs text-gray-500 mt-1">
                Last claim: {new Date(tokens.last_claim_at).toLocaleString()}
              </div>
            )}
            {claimError && (
              <div className="text-xs text-red-400 mt-2">{claimError}</div>
            )}
          </div>
          <div className="text-right">
            {tokens && tokens.tokens >= 1 && (
              <div className="text-xs text-gray-500 mb-2">
                You receive ≈ {(tokens.tokens * 0.9995).toFixed(6)} NEXORA
              </div>
            )}
            <button
              onClick={handleClaim}
              disabled={claiming || !tokens || tokens.tokens < 1 || !user?.wallet_address}
              className="bg-nexora-accent text-black font-semibold px-5 py-2 rounded-lg text-sm hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {claiming ? "Confirm in wallet..." : "Claim NEXORA"}
            </button>
            {!user?.wallet_address && (
              <div className="text-xs text-gray-500 mt-1">Link wallet first</div>
            )}
          </div>
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
