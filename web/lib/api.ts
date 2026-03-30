const API = process.env.NEXT_PUBLIC_API_URL!;

export interface UserInfo {
  id: number;
  username: string;
  referral_code: string;
  wallet_address: string | null;
  points: number;
  total_earned: number;
  created_at: string;
}

export interface NodeInfo {
  node_id: string;
  device_id: string;
  uptime: number;
  last_seen: string;
  status: string;
  node_score: number;
  ip_address: string | null;
}

export interface ChainNodeInfo {
  chain_node_id: string;
  chain_id: number;
  chain_name: string;
  last_block: number;
  sync_lag: number;
  status: string;
  last_verified: string | null;
}

export interface PointsInfo {
  username: string;
  points: number;
  total_earned: number;
}

export async function getUser(username: string): Promise<UserInfo | null> {
  const r = await fetch(`${API}/user/${username}`, { cache: "no-store" });
  if (!r.ok) return null;
  return r.json();
}

export async function getPoints(username: string): Promise<PointsInfo | null> {
  const r = await fetch(`${API}/points/${username}`, { cache: "no-store" });
  if (!r.ok) return null;
  return r.json();
}

export async function getUserNodes(username: string): Promise<NodeInfo[]> {
  const r = await fetch(`${API}/node/user/${username}`, { cache: "no-store" });
  if (!r.ok) return [];
  return r.json();
}

export async function getChainNodes(nodeId: string): Promise<ChainNodeInfo[]> {
  const r = await fetch(`${API}/chain/nodes/${nodeId}`, { cache: "no-store" });
  if (!r.ok) return [];
  return r.json();
}

export async function linkWallet(username: string, walletAddress: string): Promise<UserInfo | null> {
  const r = await fetch(`${API}/user/${username}/wallet`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wallet_address: walletAddress }),
  });
  if (!r.ok) {
    const err = await r.json();
    throw new Error(err.detail || "Failed to link wallet");
  }
  return r.json();
}

export async function getSupportedChains() {
  const r = await fetch(`${API}/chain/supported`, { cache: "force-cache" });
  if (!r.ok) return [];
  return r.json();
}

export function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function timeAgo(dateStr: string): string {
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}
