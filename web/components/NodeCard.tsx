"use client";
import { NodeInfo, ChainNodeInfo, formatUptime, timeAgo } from "../lib/api";

const CHAIN_NAMES: Record<string, string> = {
  eth_mainnet: "ETH", op_mainnet: "OP", bnb_mainnet: "BNB",
  base_mainnet: "Base", base_sepolia: "Base Sepolia",
  eth_sepolia: "ETH Sepolia", op_sepolia: "OP Sepolia", bnb_testnet: "BNB Testnet",
};

const MULTIPLIERS: Record<string, number> = {
  eth_mainnet: 5, base_mainnet: 3, op_mainnet: 2, bnb_mainnet: 2,
  base_sepolia: 1.5, eth_sepolia: 1.5, op_sepolia: 1.5, bnb_testnet: 1.2,
};

function StatusDot({ status }: { status: string }) {
  const color = status === "active" ? "bg-nexora-green" : status === "stopped" ? "bg-gray-500" : "bg-nexora-red";
  return <span className={`inline-block w-2 h-2 rounded-full ${color} mr-2`} />;
}

export function NodeCard({ node, chains }: { node: NodeInfo; chains: ChainNodeInfo[] }) {
  return (
    <div className="bg-nexora-card border border-nexora-border rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center">
            <StatusDot status={node.status} />
            <span className="font-mono text-sm text-gray-300">{node.node_id.slice(0, 16)}...</span>
          </div>
          <div className="text-xs text-gray-500 mt-1">Last seen {timeAgo(node.last_seen)}</div>
        </div>
        <div className="text-right">
          <div className="text-nexora-accent font-bold">{node.node_score}/100</div>
          <div className="text-xs text-gray-500">score</div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-nexora-bg rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">Uptime</div>
          <div className="font-semibold">{formatUptime(node.uptime)}</div>
        </div>
        <div className="bg-nexora-bg rounded-lg p-3">
          <div className="text-xs text-gray-500 mb-1">IP</div>
          <div className="font-semibold text-sm">{node.ip_address || "—"}</div>
        </div>
      </div>

      {/* Chain nodes */}
      {chains.length > 0 && (
        <div>
          <div className="text-xs text-gray-500 mb-2">Blockchain Nodes</div>
          <div className="flex flex-wrap gap-2">
            {chains.map(cn => (
              <div key={cn.chain_node_id}
                className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs border ${
                  cn.status === "active" ? "border-nexora-green/30 bg-nexora-green/10 text-nexora-green"
                  : "border-gray-700 bg-gray-800 text-gray-400"
                }`}>
                <StatusDot status={cn.status} />
                {CHAIN_NAMES[cn.chain_name] || cn.chain_name}
                <span className="text-gray-400 ml-1">{MULTIPLIERS[cn.chain_name] || 1}×</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
